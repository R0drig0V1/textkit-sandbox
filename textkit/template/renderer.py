"""Renderer of the template engine (plan task T3.4) and the public ``render``.

``render`` parses the whole template first (``textkit/template/parser.py``), so a syntax
error is raised before any output is produced, then walks the tree with the context.

Names are looked up in a chain of scopes: the innermost ``for`` first (its loop variable and
``loop``), then the enclosing loops, then the context. So a loop variable hides a context key
of the same name, and ``loop`` is always the innermost loop. What a missing name does is
decided in the ADR "template missing names" (docs/decisions/*-template-missing-names.md):
an error in ``{{ }}`` and ``for``, false in ``if``.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from textkit.template import filters
from textkit.template.errors import TemplateError
from textkit.template.parser import Expr, For, If, Node, Output, Text, parse

Scope = Dict[str, Any]


def render(template: str, context: dict[str, Any]) -> str:
    """Fill ``template`` with values from ``context`` and return the text.

    Syntax (full reference: ``docs/template.md``): ``{{ name }}`` prints a value, with a
    dotted name (``user.name``, through dict keys only) and optional filters
    (``{{ title | slug | truncate:20 }}``); ``{% if x %}...{% else %}...{% endif %}`` tests
    Python truth; ``{% for item in items %}...{% endfor %}`` loops over a list, with
    ``loop.index`` counting from 1; ``{# ... #}`` is a comment. Text outside tags is copied
    exactly (``"\\r\\n"`` included) and nothing is HTML-escaped. A value prints as
    ``str(value)``, ``None`` as ``""``; filters apply to that text.

    Missing names (ADR "template missing names"): an error in ``{{ }}`` and ``for``, false
    in ``if``.

    Raises:
        TypeError: if ``template`` is not a ``str`` or ``context`` is not a ``dict``.
        TemplateSyntaxError: for invalid syntax, before anything is rendered.
        TemplateError: for a name missing from the context in ``{{ }}`` or ``for``, a
            ``for`` over a value that is not a ``list``, and a dotted name through a value
            that is not a ``dict``.
        Both errors carry ``line`` and ``column`` (from 1) of the tag at fault.
    """
    if not isinstance(template, str):
        raise TypeError(f"template must be a str, not {type(template).__name__}")
    if not isinstance(context, dict):
        raise TypeError(f"context must be a dict, not {type(context).__name__}")
    out: List[str] = []
    render_nodes(parse(template), [context], out)
    return "".join(out)


def render_nodes(nodes: Sequence[Node], scopes: List[Scope], out: List[str]) -> None:
    """Append the output of ``nodes`` to ``out``; ``scopes`` is innermost last.

    Raises ``TemplateError`` as ``render`` documents.
    """
    for node in nodes:
        if isinstance(node, Text):
            out.append(node.text)
        elif isinstance(node, Output):
            value, missing = resolve(node.expr, scopes, node)
            if missing is not None:
                raise TemplateError(missing, node.line, node.column)
            out.append(apply_filters(node.expr, value))
        elif isinstance(node, If):
            value, missing = resolve(node.expr, scopes, node)
            if missing is not None:
                truth = False  # a missing name is false in an if (ADR)
            elif node.expr.filters:
                truth = bool(apply_filters(node.expr, value))
            else:
                truth = bool(value)
            render_nodes(node.body if truth else node.orelse, scopes, out)
        else:
            assert isinstance(node, For)
            _render_for(node, scopes, out)


def _render_for(node: For, scopes: List[Scope], out: List[str]) -> None:
    """Render a ``for`` block: its body once per item, in a new innermost scope."""
    value, missing = resolve(node.expr, scopes, node)
    if missing is not None:
        raise TemplateError(missing, node.line, node.column)
    if node.expr.filters:
        # Filters give text, never a list.
        raise TemplateError(
            "'for' needs a list, but filters turn its value into text", node.line, node.column
        )
    if not isinstance(value, list):
        raise TemplateError(
            f"'for' needs a list, but {_dotted(node.expr.names)!r} is a "
            f"{type(value).__name__}",
            node.line,
            node.column,
        )
    for index, item in enumerate(value, 1):
        # "loop" is a dict so that loop.index follows the same dotted-name rule as the rest.
        scopes.append({node.target: item, "loop": {"index": index}})
        try:
            render_nodes(node.body, scopes, out)
        finally:
            scopes.pop()


def resolve(
    expr: Expr, scopes: List[Scope], node: Union[Output, If, For]
) -> Tuple[Any, Optional[str]]:
    """Look up the dotted name of ``expr``; return ``(value, None)`` or ``(None, message)``.

    The message describes the missing name; the caller decides whether that is an error
    (``{{ }}``, ``for``) or false (``if``).

    Raises:
        TemplateError: at ``node``'s position, when a part of the name is reached through a
            value that is not a ``dict`` (missing or not, this is an error everywhere).
    """
    first, *rest = expr.names
    for scope in reversed(scopes):
        if first in scope:
            value = scope[first]
            break
    else:
        return None, f"name {first!r} is not defined"
    for depth, name in enumerate(rest, 1):
        if not isinstance(value, dict):
            raise TemplateError(
                f"{_dotted(expr.names[:depth])!r} is a {type(value).__name__}, not a dict, "
                f"so it has no key {name!r}",
                node.line,
                node.column,
            )
        if name not in value:
            return None, f"{_dotted(expr.names[:depth])!r} has no key {name!r}"
        value = value[name]
    return value, None


def apply_filters(expr: Expr, value: Any) -> str:
    """The printed text of ``value`` (``""`` for ``None``) passed through ``expr``'s filters."""
    text = "" if value is None else str(value)
    for flt in expr.filters:
        text = filters.apply(flt.name, flt.width, text)
    return text


def _dotted(names: Sequence[str]) -> str:
    """``("user", "name")`` -> ``"user.name"``."""
    return ".".join(names)
