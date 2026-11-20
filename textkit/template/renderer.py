"""Renderer of ``textkit.template``: fills a parsed template with a context (plan task T3.4).

``render(template, context)`` parses the template (every syntax error comes first, before
any output is built) and walks the tree. Names are looked up in a stack of scopes: the
context at the bottom, and one scope per enclosing ``for`` holding its variable and
``loop`` (``{"index": n}``, from 1), so the innermost loop wins and ``loop`` hides a context
key of that name.

Missing names follow ADR 0007 (``docs/decisions/0007-template-missing-names.md``): an error
in ``{{ }}`` and ``for``, false in ``if``. Values print as ``str(value)``, except ``None``,
which prints as ``""``. Output is plain text: nothing is escaped.
"""

from typing import Any, Dict, List, NoReturn, Union

from textkit.template import filters
from textkit.template.exceptions import TemplateError
from textkit.template.parser import Expression, For, If, Node, Output, Text, parse

# Returned by _lookup for a name that is not there (None is a value a context may hold).
_MISSING = object()

_Scopes = List[Dict[str, Any]]


def render(template: str, context: dict[str, Any]) -> str:
    """Render ``template`` with the values in ``context`` and return the text.

    Syntax: ``{{ expr }}`` prints a value; ``{% if expr %} ... {% else %} ... {% endif %}``
    tests it with Python's ``bool``; ``{% for item in expr %} ... {% endfor %}`` repeats over
    a list, with ``loop.index`` (from 1) inside; ``{# ... #}`` is a comment. ``expr`` is a
    dotted name that follows dict keys (``user.name``) with optional filters
    (``{{ title | slug | truncate:20 }}``; the filters are listed in ``docs/template.md``).
    Text outside tags is copied as is, ``"\\r\\n"`` included, and nothing is HTML-escaped.

    A value prints as ``str(value)``, ``None`` as ``""``; filters apply to that string.
    A name missing from the context is an error in ``{{ }}`` and ``for`` and false in
    ``if`` (ADR 0007).

    Raises:
        TypeError: if ``template`` is not a ``str`` or ``context`` is not a ``dict``.
        TemplateSyntaxError: if the template cannot be parsed (raised before rendering).
        TemplateError: for a missing name in ``{{ }}`` or ``for``, a ``for`` over a value
            that is not a list, a dotted name through a value that is not a dict, or a value
            whose ``str`` raises ``ValueError`` (an int of more than 4300 digits on Python
            3.11+). The error's ``line`` and ``column`` are those of the tag's opening
            delimiter.
    """
    if not isinstance(template, str):
        raise TypeError(f"template must be a str, not {type(template).__name__}")
    if not isinstance(context, dict):
        raise TypeError(f"context must be a dict, not {type(context).__name__}")
    nodes = parse(template)
    out: List[str] = []
    _render(nodes, [context], out)
    return "".join(out)


def _render(nodes: List[Node], scopes: _Scopes, out: List[str]) -> None:
    """Append the output of ``nodes`` to ``out``; recursion depth is bounded by the parser."""
    for node in nodes:
        if isinstance(node, Text):
            out.append(node.text)
        elif isinstance(node, Output):
            value = _lookup(node.expression, scopes, node)
            if value is _MISSING:
                _missing(node.expression, node)
            out.append(_text(value, node))
        elif isinstance(node, If):
            value = _lookup(node.expression, scopes, node)
            # A missing name is false, whatever the filters (ADR 0007).
            truth = value is not _MISSING and (
                bool(_text(value, node)) if node.expression.filters else bool(value)
            )
            _render(node.body if truth else node.orelse, scopes, out)
        else:
            _render_for(node, scopes, out)


def _render_for(node: For, scopes: _Scopes, out: List[str]) -> None:
    """Render ``node``'s body once per item of its list, in a scope of its own."""
    value = _lookup(node.expression, scopes, node)
    if value is _MISSING:
        _missing(node.expression, node)
    if node.expression.filters:
        # Filters give a string, never a list; say so instead of "not a list: str".
        raise TemplateError(
            f"'for' needs a list, but filters turn {node.expression.dotted!r} into text",
            node.line,
            node.column,
        )
    if not isinstance(value, list):
        raise TemplateError(
            f"'for' needs a list, but {node.expression.dotted!r} is a {type(value).__name__}",
            node.line,
            node.column,
        )
    for index, item in enumerate(value, 1):
        scopes.append({node.target: item, "loop": {"index": index}})
        try:
            _render(node.body, scopes, out)
        finally:
            scopes.pop()


def _lookup(expression: Expression, scopes: _Scopes, node: Any) -> Any:
    """Return the value of ``expression``'s dotted name, or ``_MISSING``.

    The first segment is looked up from the innermost scope outwards; each following segment
    is a key of the dict found so far. A key that is not there gives ``_MISSING``; a value
    that is not a ``dict`` before the last segment raises ``TemplateError`` at ``node``.
    """
    first, *rest = expression.names
    for scope in reversed(scopes):
        if first in scope:
            value = scope[first]
            break
    else:
        return _MISSING
    for depth, key in enumerate(rest, 1):
        if not isinstance(value, dict):
            prefix = ".".join(expression.names[:depth])
            raise TemplateError(
                f"cannot look up {key!r} in {prefix!r}: it is a {type(value).__name__}, "
                "not a dict",
                node.line,
                node.column,
            )
        if key not in value:
            return _MISSING
        value = value[key]
    return value


def _missing(expression: Expression, node: Any) -> NoReturn:
    """Raise the ``TemplateError`` for a missing name at ``node`` (ADR 0007)."""
    raise TemplateError(f"{expression.dotted!r} is not defined", node.line, node.column)


def _text(value: Any, node: Union[Output, If]) -> str:
    """Turn ``value`` into text (``None`` -> ``""``) and apply ``node``'s filters.

    ``str(value)`` raises ``ValueError`` for an int of more than 4300 digits (alone or inside
    a list or dict) from Python 3.11 and the 3.9.14+ security releases; it becomes a
    ``TemplateError`` at ``node``, so no standard-library ``ValueError`` escapes (phase 3
    rule "Errors").
    """
    try:
        text = "" if value is None else str(value)
    except ValueError as exc:
        raise TemplateError(
            f"cannot print {node.expression.dotted!r}: {exc}", node.line, node.column
        ) from exc
    for f in node.expression.filters:
        text = filters.apply(f.name, f.width, text)
    return text
