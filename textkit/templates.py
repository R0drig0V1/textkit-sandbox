"""Template helpers. Every public function is listed in the README's function table.

``render`` fills ``{name}`` placeholders from a mapping with a small grammar of its own
(plan task T3.12, docs/phases/phase-3-converters.md). It deliberately does not use
``str.format`` or ``str.format_map``: those apply format specs and conversions (``{x:>5}``,
``{x!r}``) and follow attribute and index paths (``{a.b}``, ``{a[0]}``), so a template could
reach into the values it is given. Here every value goes through ``str()`` and nothing else.
"""

import re
from collections.abc import Mapping as _AbcMapping
from typing import Mapping, Union

# A placeholder name: ASCII letters, digits and "_", not starting with a digit. The explicit
# classes keep it ASCII (``\w`` would accept any Unicode letter or digit).
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class _Placeholder(str):
    """A parsed ``{name}``; a subclass of ``str`` only to tell it apart from literal text."""


def _parse(template: str) -> list[Union[str, _Placeholder]]:
    """Split ``template`` into literal text and placeholders, scanning left to right.

    Raises ``ValueError`` for an unmatched ``{`` or ``}`` and for brace content that is not
    a name, so the whole template is validated before any value is looked up.
    """
    parts: list[Union[str, _Placeholder]] = []
    literal: list[str] = []
    i, n = 0, len(template)
    while i < n:
        char = template[i]
        if char not in "{}":
            literal.append(char)
            i += 1
        elif template.startswith(char * 2, i):
            # "{{" and "}}" are checked first, so "{{{x}}}" reads as "{{", "{x}", "}}".
            literal.append(char)
            i += 2
        elif char == "}":
            raise ValueError(f"render(): unmatched '}}' at index {i}")
        else:
            end = template.find("}", i + 1)
            if end == -1:
                raise ValueError(f"render(): unmatched '{{' at index {i}")
            name = template[i + 1:end]
            # fullmatch, not match with "$", which would accept a trailing newline.
            if not _NAME.fullmatch(name):
                raise ValueError(f"render(): invalid placeholder {{{name}}} at index {i}")
            parts.append("".join(literal))
            literal = []
            parts.append(_Placeholder(name))
            i = end + 1
    parts.append("".join(literal))
    return parts


def render(template: str, values: Mapping[str, object]) -> str:
    """Return ``template`` with every ``{name}`` placeholder replaced by ``str(values[name])``.

    The template is scanned left to right: ``{{`` and ``}}`` stand for a literal ``{`` and
    ``}``, and a placeholder is ``{`` + a name matching ``[A-Za-z_][A-Za-z0-9_]*`` + ``}``
    (so ``render("{{{x}}}", {"x": 1})`` is ``"{1}"``). Values are converted with ``str()``
    only: format specs, conversions, attribute access and indexing are not supported, and
    the result of ``str()`` is inserted as is, never parsed again. Text with no braces is
    returned unchanged.

    Raises ``ValueError`` for any other brace content (empty, digits, spaces, ``.``, ``[``,
    ``!``, ``:``, as in ``"{}"``, ``"{0}"``, ``"{ x }"``, ``"{a.b}"``, ``"{x:>5}"``) and for
    an unmatched ``{`` or ``}``. The whole template is validated before any lookup, so a
    ``ValueError`` wins over a missing name. Raises ``KeyError(name)`` for the first name,
    from the left, that ``values`` does not contain, and ``TypeError`` if ``template`` is not
    a ``str`` or ``values`` is not a mapping.
    """
    if not isinstance(template, str):
        raise TypeError(f"render() expects a str template, got {type(template).__name__}")
    if not isinstance(values, _AbcMapping):
        raise TypeError(f"render() expects a mapping of values, got {type(values).__name__}")
    parts = _parse(template)
    out = []
    for part in parts:
        if not isinstance(part, _Placeholder):
            out.append(part)
            continue
        name = str(part)
        try:
            value = values[name]
        except KeyError:
            # Re-raised so the error is exactly KeyError(name), whatever the mapping raised.
            raise KeyError(name) from None
        out.append(str(value))
    return "".join(out)
