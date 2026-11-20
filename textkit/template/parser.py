"""Parser of ``textkit.template``: turns the lexer's tokens into a tree of nodes (T3.4).

The tree has four node types: ``Text`` (copied as is), ``Output`` (``{{ expr }}``), ``If``
(``{% if expr %} ... {% else %} ... {% endif %}``) and ``For``
(``{% for name in expr %} ... {% endfor %}``). An expression is a dotted name with optional
filters, ``user.name | slug | truncate:20``; the same grammar is used in all three places.

Every syntax error is found here, before anything is rendered, so a template either renders
or fails at once with a ``TemplateSyntaxError`` that points at the opening delimiter of the
offending tag (for a block with no end tag, at its opening tag; when several are open, the
innermost). Filters are checked here too (``filters.check``), so the renderer never meets an
unknown filter or a bad ``truncate`` width.

The parser keeps an explicit stack of open blocks rather than recursing, and limits nesting
to ``MAX_DEPTH`` blocks: the renderer does recurse, and the limit keeps it far from Python's
recursion limit, so a deep template is a syntax error, not a ``RecursionError``.
"""

import re
from dataclasses import dataclass, field
from typing import List, NoReturn, Optional, Tuple, Union

from textkit.template import filters
from textkit.template.exceptions import TemplateSyntaxError
from textkit.template.lexer import BLOCK, TEXT, Token, tokenize

# Deepest nesting of if/for blocks a template may have.
MAX_DEPTH = 100

# "for <name> in <expression>"; the expression is everything after "in" and is parsed apart.
_FOR = re.compile(r"for\s+(\S+)\s+in\s+(.+)", re.S)


@dataclass(frozen=True)
class Filter:
    """One filter of an expression: its name and, for ``truncate``, its width."""

    name: str
    width: Optional[int] = None


@dataclass(frozen=True)
class Expression:
    """A dotted name (``names``, one item per segment) and the filters applied in order."""

    names: Tuple[str, ...]
    filters: Tuple[Filter, ...] = ()

    @property
    def dotted(self) -> str:
        """The name as written in the template, without filters (``"user.name"``)."""
        return ".".join(self.names)


@dataclass
class Text:
    """Text outside tags, copied to the output as is."""

    text: str


@dataclass
class Output:
    """``{{ expression }}`` at ``line``, ``column`` (its ``{{``)."""

    expression: Expression
    line: int
    column: int


@dataclass
class If:
    """``{% if expression %} body {% else %} orelse {% endif %}`` (``orelse`` may be empty)."""

    expression: Expression
    line: int
    column: int
    body: List["Node"] = field(default_factory=list)
    orelse: List["Node"] = field(default_factory=list)
    has_else: bool = False


@dataclass
class For:
    """``{% for target in expression %} body {% endfor %}``."""

    target: str
    expression: Expression
    line: int
    column: int
    body: List["Node"] = field(default_factory=list)


Node = Union[Text, Output, If, For]


def parse(template: str) -> List[Node]:
    """Parse ``template`` into a list of nodes (the top level of the tree).

    Raises:
        TemplateSyntaxError: for an unterminated ``{{``, ``{%`` or ``{#`` (from the lexer);
            an empty tag; an unknown tag; a malformed ``if`` or ``for``; an invalid
            expression; an unknown filter or a bad filter argument; ``else``, ``endif`` or
            ``endfor`` without their opening tag (or a second ``else`` in one ``if``); a
            block with no end tag; and nesting deeper than ``MAX_DEPTH``. The position is
            that of the offending tag's opening delimiter.
    """
    root: List[Node] = []
    body = root
    # Open blocks, innermost last, each with the body it was appended to, which becomes
    # the current body again when the block closes.
    stack: List[Tuple[Union[If, For], List[Node]]] = []
    for token in tokenize(template):
        if token.kind == TEXT:
            body.append(Text(token.value))
        elif token.kind != BLOCK:
            body.append(Output(_expression(token.value, token), token.line, token.column))
        else:
            body = _block(token, body, stack)
    if stack:
        node = stack[-1][0]
        tag, end = ("if", "endif") if isinstance(node, If) else ("for", "endfor")
        raise TemplateSyntaxError(f"{tag!r} has no {end!r}", node.line, node.column)
    return root


def _block(
    token: Token, body: List[Node], stack: List[Tuple[Union[If, For], List[Node]]]
) -> List[Node]:
    """Handle one block tag; return the body that the following nodes go into."""
    if not token.value:
        _fail("empty tag", token)
    # Split once on any whitespace, so "if\tx" and "if\nx" work like "if x".
    parts = token.value.split(None, 1)
    name, rest = parts[0], (parts[1] if len(parts) > 1 else "")
    if name in ("if", "for"):
        if len(stack) >= MAX_DEPTH:
            _fail(f"blocks nested deeper than {MAX_DEPTH}", token)
        node: Union[If, For]
        if name == "if":
            if not rest:
                _fail("'if' needs an expression: {% if <expression> %}", token)
            node = If(_expression(rest, token), token.line, token.column)
        else:
            node = _for(token)
        body.append(node)
        stack.append((node, body))
        return node.body
    if name in ("else", "endif", "endfor"):
        opener = "for" if name == "endfor" else "if"
        if not stack or (opener == "if") != isinstance(stack[-1][0], If):
            _fail(f"{name!r} without a matching {opener!r}", token)
        if rest:
            _fail(f"{name!r} takes nothing after it", token)
        node, parent = stack[-1]
        if name != "else":
            stack.pop()
            return parent
        assert isinstance(node, If)
        if node.has_else:
            _fail("a second 'else' in the same 'if'", token)
        node.has_else = True
        return node.orelse
    _fail(f"unknown tag {name!r}", token)


def _for(token: Token) -> For:
    """Parse ``for <name> in <expression>``; the name is a plain (undotted) identifier."""
    match = _FOR.fullmatch(token.value)
    if match is None:
        _fail("malformed 'for': expected {% for <name> in <expression> %}", token)
    target, source = match.groups()
    if not target.isidentifier():
        _fail(f"invalid loop variable {target!r}: it must be a plain name", token)
    if target == "loop":
        # Inside the loop, "loop" is the loop itself and would hide the item.
        _fail("'loop' cannot be a loop variable: it names the loop itself", token)
    return For(target, _expression(source, token), token.line, token.column)


def _expression(source: str, token: Token) -> Expression:
    """Parse ``name.name | filter | filter:arg``; whitespace around each part is ignored."""
    head, *tail = source.split("|")
    head = head.strip()
    if not head:
        _fail("missing name in expression", token)
    names = tuple(head.split("."))
    if not all(name.isidentifier() for name in names):
        _fail(f"invalid name {head!r}: expected names separated by '.'", token)
    parsed: List[Filter] = []
    for part in tail:
        name, colon, argument = (piece.strip() for piece in part.partition(":"))
        if not name:
            _fail("missing filter name after '|'", token)
        problem = filters.check(name, argument if colon else None)
        if problem:
            _fail(problem, token)
        parsed.append(Filter(name, filters.width(argument) if colon else None))
    return Expression(names, tuple(parsed))


def _fail(message: str, token: Token) -> NoReturn:
    """Raise a ``TemplateSyntaxError`` at ``token``'s position."""
    raise TemplateSyntaxError(message, token.line, token.column)
