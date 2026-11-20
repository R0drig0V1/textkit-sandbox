"""Parser of the template engine (plan task T3.4): tokens -> a tree of nodes.

The tree is a list of nodes, each one of:

- ``Text``: text copied as is;
- ``Output``: ``{{ expr }}``;
- ``If``: ``{% if expr %} body {% else %} orelse {% endif %}`` (``orelse`` is ``[]`` when
  there is no ``else``);
- ``For``: ``{% for target in expr %} body {% endfor %}``.

An expression (``Expr``) is a dotted name (``user.name``: each part a Python identifier)
followed by zero or more filters (``| slug``, ``| truncate:20``). There are no literals,
operators or calls. Every syntax error is found here, before anything is rendered, so a bad
template fails the same way whatever its context.

The parser is iterative (a stack of open blocks), so deep nesting cannot exhaust Python's
recursion limit while parsing.
"""

import re
from typing import List, NamedTuple, Optional, Tuple, Union

from textkit.template import filters
from textkit.template.errors import TemplateSyntaxError
from textkit.template.lexer import BLOCK, OUTPUT, TEXT, Token, tokenize

# "for <target> in <expr>": the target and the expression, whitespace of any kind between.
_FOR = re.compile(r"for\s+(\S+)\s+in\s+(.*)", re.S)

# A truncate width: an optional sign and ASCII digits. int() alone would also accept
# "1_000", " 5" or non-ASCII digits, which are not part of the syntax.
_INTEGER = re.compile(r"[+-]?[0-9]+")

# The loop information object is reachable as "loop"; a loop variable of that name could
# never be read, so it is rejected.
_LOOP = "loop"


class Filter(NamedTuple):
    """One filter of an expression: its name, and the width for ``truncate`` (else ``None``)."""

    name: str
    width: Optional[int]


class Expr(NamedTuple):
    """A dotted name and its filters: ``title | truncate:20`` is
    ``Expr(("title",), (Filter("truncate", 20),))``."""

    names: Tuple[str, ...]
    filters: Tuple[Filter, ...]


class Text(NamedTuple):
    """Text outside tags, copied to the output as is."""

    text: str


class Output(NamedTuple):
    """``{{ expr }}`` at ``line``:``column`` (its ``{{``)."""

    expr: Expr
    line: int
    column: int


class If(NamedTuple):
    """``{% if expr %}`` at ``line``:``column``, its body and its ``else`` body."""

    expr: Expr
    body: List["Node"]
    orelse: List["Node"]
    line: int
    column: int


class For(NamedTuple):
    """``{% for target in expr %}`` at ``line``:``column`` and its body."""

    target: str
    expr: Expr
    body: List["Node"]
    line: int
    column: int


Node = Union[Text, Output, If, For]


class _Open:
    """A block whose end tag has not been seen yet (one entry of the parser's stack)."""

    def __init__(self, tag: str, token: Token, expr: Expr, target: str = "") -> None:
        self.tag = tag  # "if" or "for"
        self.token = token  # the opening tag, for positions
        self.expr = expr
        self.target = target
        self.body: List[Node] = []
        self.orelse: Optional[List[Node]] = None  # set by {% else %}

    def current(self) -> List[Node]:
        """The list that new nodes go into: the else body once ``else`` was seen."""
        return self.body if self.orelse is None else self.orelse


def _error(message: str, token: Token) -> TemplateSyntaxError:
    """A syntax error located at ``token``'s opening delimiter."""
    return TemplateSyntaxError(message, token.line, token.column)


def parse_expr(source: str, token: Token) -> Expr:
    """Parse ``source``, the expression of ``token``, into an ``Expr``.

    Spaces around ``|`` and ``:`` are optional; the dotted name itself may not contain
    spaces. Filter names and arguments are checked against the fixed table in
    ``textkit/template/filters.py``.

    Raises:
        TemplateSyntaxError: at ``token``'s position, for an empty or malformed name, an
            empty or unknown filter, ``truncate`` without a width, with a width that is not
            an integer or is below 3, and an argument given to a filter that takes none.
    """
    path, *parts = source.split("|")
    path = path.strip()
    if not path:
        raise _error("expected a name", token)
    names = tuple(path.split("."))
    if not all(name.isidentifier() for name in names):
        raise _error(f"invalid name {path!r}", token)
    found: List[Filter] = []
    for part in parts:
        name, colon, argument = (piece.strip() for piece in part.partition(":"))
        if not name:
            raise _error(f"expected a filter name after '|' in {source!r}", token)
        if name == filters.TRUNCATE:
            found.append(Filter(name, _truncate_width(argument, bool(colon), token)))
        elif name in filters.NO_ARGUMENT:
            if colon:
                raise _error(f"filter {name!r} takes no argument", token)
            found.append(Filter(name, None))
        else:
            raise _error(
                f"unknown filter {name!r} (filters: {', '.join(filters.NAMES)})", token
            )
    return Expr(names, tuple(found))


def _truncate_width(argument: str, has_colon: bool, token: Token) -> int:
    """Check and convert the argument of ``truncate``; see ``parse_expr`` for the errors."""
    if not has_colon or not argument:
        raise _error("filter 'truncate' needs a width: truncate:<width>", token)
    if not _INTEGER.fullmatch(argument):
        raise _error(f"truncate width must be an integer, got {argument!r}", token)
    try:
        width = int(argument)
    except ValueError:
        # Only when the digits exceed int()'s string limit (Python 3.11+): a ValueError
        # from the standard library never escapes textkit (phase 3 rule "Errors").
        raise _error("truncate width is too large", token) from None
    if width < filters.MIN_TRUNCATE_WIDTH:
        raise _error(
            f"truncate width must be at least {filters.MIN_TRUNCATE_WIDTH}, got {width}",
            token,
        )
    return width


def parse(template: str) -> List[Node]:
    """Tokenize and parse ``template`` into a list of nodes (see the module docstring).

    Raises:
        TemplateSyntaxError: for every syntax error, at the position of the opening
            delimiter of the tag at fault: the lexer's unterminated tags; a malformed
            expression (``parse_expr``); an empty or unknown block tag; ``if`` without an
            expression; a ``for`` not of the form ``for <name> in <expr>``, or whose loop
            variable is ``loop``; an argument after ``else``, ``endif`` or ``endfor``; an
            ``else``, ``endif`` or ``endfor`` that does not belong to the innermost open
            block (including a second ``else``); and, at the end, a block with no end tag
            (at its opening tag; the innermost one when several are open).
    """
    root: List[Node] = []
    stack: List[_Open] = []
    for token in tokenize(template):
        current = stack[-1].current() if stack else root
        if token.kind == TEXT:
            current.append(Text(token.value))
        elif token.kind == OUTPUT:
            current.append(Output(parse_expr(token.value, token), token.line, token.column))
        else:
            assert token.kind == BLOCK
            _block(token, stack, root)
    if stack:
        block = stack[-1]
        raise _error(f"{block.tag!r} is never closed with 'end{block.tag}'", block.token)
    return root


def _block(token: Token, stack: List[_Open], root: List[Node]) -> None:
    """Handle one ``{% ... %}`` tag: open, switch or close a block on ``stack``."""
    words = token.value.split(None, 1)
    if not words:
        raise _error("empty tag", token)
    tag = words[0]
    rest = words[1] if len(words) > 1 else ""
    if tag == "if":
        if not rest:
            raise _error("'if' needs an expression", token)
        stack.append(_Open("if", token, parse_expr(rest, token)))
    elif tag == "for":
        match = _FOR.fullmatch(token.value)
        if match is None or not match.group(2).strip():
            raise _error("expected 'for <name> in <expression>'", token)
        target = match.group(1)
        if not target.isidentifier():
            raise _error(f"invalid loop variable {target!r}", token)
        if target == _LOOP:
            raise _error("'loop' is reserved and cannot be a loop variable", token)
        stack.append(_Open("for", token, parse_expr(match.group(2), token), target))
    elif tag in ("else", "endif", "endfor"):
        if rest:
            raise _error(f"{tag!r} takes no arguments", token)
        opener = "for" if tag == "endfor" else "if"
        if not stack:
            raise _error(f"{tag!r} without an opening {opener!r}", token)
        block = stack[-1]
        if block.tag != opener:
            raise _error(
                f"{tag!r} found while the {block.tag!r} at line {block.token.line}, "
                f"column {block.token.column} is still open",
                token,
            )
        if tag == "else":
            if block.orelse is not None:
                raise _error("'if' already has an 'else'", token)
            block.orelse = []
            return
        stack.pop()
        parent = stack[-1].current() if stack else root
        line, column = block.token.line, block.token.column
        if block.tag == "if":
            parent.append(If(block.expr, block.body, block.orelse or [], line, column))
        else:
            parent.append(For(block.target, block.expr, block.body, line, column))
    else:
        raise _error(f"unknown tag {tag!r}", token)
