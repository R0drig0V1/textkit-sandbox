"""The filters of ``textkit.template``: a fixed table over existing textkit functions (T3.4).

A filter turns a string into a string. In ``{{ title | slug | truncate:20 }}`` the value is
first turned into text (``str(value)``, ``None`` as ``""``) and then each filter is applied
from left to right. The table is closed: templates cannot add filters, so a template can only
call the functions listed here.

``truncate`` is the only filter with an argument, the width (``truncate:<width>``); its suffix
is always ``"..."``. The parser checks every filter name and argument with ``check`` before
anything is rendered, so ``apply`` never meets a bad one and ``truncate``'s own
``ValueError`` (width below the suffix length) cannot escape while rendering.
"""

from typing import Callable, Dict, Optional

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case
from textkit.strings import slugify, squeeze, strip_accents, truncate

# Filters without an argument, by template name.
_PLAIN: Dict[str, Callable[[str], str]] = {
    "camel": to_camel_case,
    "kebab": to_kebab_case,
    "lower": str.lower,
    "slug": slugify,
    "snake": to_snake_case,
    "squeeze": squeeze,
    "strip_accents": strip_accents,
    "upper": str.upper,
}

# The smallest width truncate accepts: the length of its default suffix "...".
MIN_TRUNCATE_WIDTH = 3

NAMES = tuple(sorted([*_PLAIN, "truncate"]))


def check(name: str, argument: Optional[str]) -> Optional[str]:
    """Return why the filter ``name`` with ``argument`` is invalid, or ``None`` if it is valid.

    ``argument`` is the text after ``:`` (stripped), or ``None`` when there was no ``:``.
    ``truncate`` needs a width written with ASCII digits only (no sign, no other digit
    scripts), at least ``MIN_TRUNCATE_WIDTH``; every other filter takes no argument. The
    width is checked as text, never with ``int()`` on arbitrary input, so no standard-library
    ``ValueError`` can escape.
    """
    if name == "truncate":
        if argument is None:
            return "filter 'truncate' needs a width: truncate:<width>"
        if not (argument.isascii() and argument.isdigit()):
            return f"filter 'truncate' needs an integer width, got {argument!r}"
        if int(argument) < MIN_TRUNCATE_WIDTH:
            return (
                f"filter 'truncate' needs a width of at least {MIN_TRUNCATE_WIDTH}, "
                f"got {int(argument)}"
            )
        return None
    if name not in _PLAIN:
        return f"unknown filter {name!r}"
    if argument is not None:
        return f"filter {name!r} takes no argument"
    return None


def apply(name: str, width: Optional[int], text: str) -> str:
    """Apply the filter ``name`` to ``text``; ``width`` is ``truncate``'s width, else ``None``.

    The filter must have passed ``check``: an unknown name raises ``KeyError``, a bug in the
    parser rather than a template error.
    """
    if name == "truncate":
        assert width is not None
        return truncate(text, width)
    return _PLAIN[name](text)
