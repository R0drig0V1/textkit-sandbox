"""English ordinal numbers. Every public function is listed in the README's function table."""

# Suffixes for a last digit of 1, 2 and 3; every other last digit takes "th".
_SUFFIXES = {1: "st", 2: "nd", 3: "rd"}


def ordinal(n: int) -> str:
    """Return ``n`` followed by its English ordinal suffix.

    ``n`` must be an ``int`` with ``n >= 0``. The suffix follows the last digit (``1st``,
    ``2nd``, ``3rd``, ``4th`` ... ``0th``), except that a number whose last two digits are
    11, 12 or 13 always takes ``th``. For example ``ordinal(1)`` is ``"1st"``,
    ``ordinal(11)`` is ``"11th"``, ``ordinal(101)`` is ``"101st"``, ``ordinal(112)`` is
    ``"112th"`` and ``ordinal(1021)`` is ``"1021st"``.

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included, a ``str`` or a
    ``float`` such as ``1.0`` too) or is negative.
    """
    # bool is a subclass of int, so it is rejected explicitly; the type is checked before
    # the sign so that "a" gets ValueError, not a TypeError from the comparison.
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"ordinal() needs an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"ordinal() needs n >= 0, got {n}")
    # 11, 12 and 13 are read "eleventh", "twelfth", "thirteenth", so the teens override the
    # last-digit rule; checking n % 100 also covers 111, 1012 and so on.
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = _SUFFIXES.get(n % 10, "th")
    return f"{n}{suffix}"
