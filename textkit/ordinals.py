"""Ordinal numbers: ``ordinal`` turns a non-negative ``int`` into its English ordinal.

Plan task T3.9 (docs/phases/phase-3-converters.md). Listed in the README's function table.
"""


def ordinal(n: int) -> str:
    """Return ``n`` followed by its English ordinal suffix (``1`` -> ``"1st"``).

    The suffix depends on the last two digits: 11, 12 and 13 take ``"th"``
    (``"11th"``, ``"112th"``); otherwise a last digit of 1, 2 or 3 takes ``"st"``,
    ``"nd"`` or ``"rd"`` (``"1021st"``, ``"2nd"``), and everything else, 0 included, takes
    ``"th"`` (``"0th"``, ``"1011th"``).

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included, although ``bool``
    subclasses ``int``) or is negative. ``ValueError`` rather than ``TypeError`` follows the
    phase-3 rule for ``int`` parameters, so every bad argument fails the same way.
    """
    # bool is checked first: isinstance(True, int) is True, but True is not a number here.
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"ordinal() expects an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"ordinal() expects n >= 0, got {n}")
    # The teens 11-13 are the exception to the last-digit rule, in every hundred.
    if n % 100 in (11, 12, 13):
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
