"""Roman numerals. Every public function is listed in the README's function table."""

# Values in descending order, the subtractive pairs (CM, CD, XC, XL, IX, IV) included, so a
# greedy walk produces the standard form: no symbol repeats more than three times and the
# only subtractions are the six pairs above.
_NUMERALS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def to_roman(n: int) -> str:
    """Return ``n`` as an upper-case Roman numeral in standard subtractive form.

    ``n`` must be an ``int`` with ``1 <= n <= 3999``: there is no Roman zero, and 4000 would
    need ``MMMM`` or an overline, neither of which is standard form. For example
    ``to_roman(4)`` is ``"IV"``, ``to_roman(1994)`` is ``"MCMXCIV"`` and ``to_roman(3999)``
    is ``"MMMCMXCIX"``.

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included, a ``str`` or a
    ``float`` such as ``4.0`` too) or is outside ``1..3999``.
    """
    # bool is a subclass of int, so it is rejected explicitly; the type is checked before
    # the range so that "a" gets ValueError, not a TypeError from the comparison.
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"to_roman() needs an int, got {type(n).__name__}")
    if not 1 <= n <= 3999:
        raise ValueError(f"to_roman() needs 1 <= n <= 3999, got {n}")
    parts = []
    for value, symbol in _NUMERALS:
        count, n = divmod(n, value)
        parts.append(symbol * count)
    return "".join(parts)
