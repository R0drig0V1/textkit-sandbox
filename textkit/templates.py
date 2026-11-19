"""Minimal string templates: ``render`` fills ``{name}`` placeholders from a mapping.

The syntax is a deliberately small subset of ``str.format``: ``{{`` and ``}}`` are literal
braces and ``{name}`` is a placeholder whose name is a Python-style identifier
(``[A-Za-z_][A-Za-z0-9_]*``). Nothing else is accepted: no positional fields, attribute or
index access, conversions or format specs. ``str.format`` and ``format_map`` are not used
because they would accept (and execute) all of those.
"""

import re
from typing import List, Mapping, Tuple

# One token per match, tried in this order at each position, so the alternatives tile the
# whole template: an escaped brace, a braced field (its content checked separately so that a
# bad field gives a precise error), a lone brace (always an error), or a run of plain text.
_TOKEN = re.compile(r"\{\{|\}\}|\{([^{}]*)\}|[{}]|[^{}]+")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def render(template: str, values: Mapping[str, object]) -> str:
    """Return ``template`` with each ``{name}`` replaced by ``str(values[name])``.

    Scanning left to right, ``{{`` and ``}}`` stand for literal ``{`` and ``}``. A
    placeholder is ``{`` + a name matching ``[A-Za-z_][A-Za-z0-9_]*`` + ``}``. Values are
    converted with ``str()`` only; format specs are never applied, and a value's text is not
    rendered again (a value of ``"{x}"`` stays ``"{x}"``).

    The whole template is validated before any value is looked up, so a syntax error wins
    over a missing name.

    Raises:
        ValueError: a brace field whose content is not a valid name (empty, digits, spaces,
            ``.``, ``[``, ``!``, ``:`` ...), or an unmatched ``{`` or ``}``.
        KeyError: ``KeyError(name)`` for the first placeholder whose name is not in
            ``values``.
        TypeError: ``template`` is not a ``str``.
    """
    if not isinstance(template, str):
        raise TypeError(f"template must be a str, not {type(template).__name__}")

    # Pass 1: tokenize and validate everything. Each piece is (is_placeholder, text).
    pieces: List[Tuple[bool, str]] = []
    for match in _TOKEN.finditer(template):
        token = match.group(0)
        if token == "{{":
            pieces.append((False, "{"))
        elif token == "}}":
            pieces.append((False, "}"))
        elif token == "{" or token == "}":
            raise ValueError(f"unmatched {token!r} at position {match.start()}")
        elif token.startswith("{"):
            name = match.group(1)
            if not _NAME.fullmatch(name):
                raise ValueError(f"invalid placeholder {token!r} at position {match.start()}")
            pieces.append((True, name))
        else:
            pieces.append((False, token))

    # Pass 2: look the names up, only once the template is known to be well formed.
    out = []
    for is_placeholder, text in pieces:
        if not is_placeholder:
            out.append(text)
            continue
        try:
            value = values[text]
        except KeyError:
            # Normalise to KeyError(name), whatever the mapping put in its own error.
            raise KeyError(text) from None
        out.append(str(value))
    return "".join(out)
