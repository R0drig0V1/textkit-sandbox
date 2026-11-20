"""The fixed filter table of the template engine (plan task T3.4).

A filter turns the printed text of a value into other text: ``{{ title | slug }}``. Every
filter is an existing textkit function or a ``str`` method; the table is fixed, so a
template cannot call anything else. The parser checks names and arguments while parsing
(``textkit/template/parser.py``), so the renderer only calls ``apply`` with valid ones.

Filters receive the value already turned into text (``str(value)``, ``""`` for ``None``),
never the value itself, so ``{{ n | upper }}`` works for a number too.
"""

from typing import Callable, Dict, Optional

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case
from textkit.strings import slugify, squeeze, strip_accents, truncate

# Filters that take no argument: name -> function of one str.
NO_ARGUMENT: Dict[str, Callable[[str], str]] = {
    "camel": to_camel_case,
    "kebab": to_kebab_case,
    "lower": str.lower,
    "slug": slugify,
    "snake": to_snake_case,
    "squeeze": squeeze,
    "strip_accents": strip_accents,
    "upper": str.upper,
}

# The one filter with an argument, truncate:<width>. Its width must be at least the length
# of truncate's default suffix ("..."): below that, textkit.strings.truncate rejects it, and
# the parser reports it at parse time instead, with the tag's position.
TRUNCATE = "truncate"
MIN_TRUNCATE_WIDTH = 3

NAMES = sorted([*NO_ARGUMENT, TRUNCATE])


def apply(name: str, width: Optional[int], text: str) -> str:
    """Apply the filter ``name`` to ``text``; ``width`` is truncate's width, else ``None``.

    The caller (the parser) has already checked the name and the width, so this never
    raises for a filter that came out of ``parse``.
    """
    if name == TRUNCATE:
        assert width is not None  # guaranteed by the parser
        return truncate(text, width)
    return NO_ARGUMENT[name](text)
