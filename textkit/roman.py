"""Roman numeral helpers. Every public function is listed in the README's function table.

``to_roman`` writes an integer from 1 to 3999 in standard subtractive form (plan task T3.3,
docs/phases/phase-3-converters.md). 3999 is the upper bound because the standard numerals
have no symbol above ``M`` (1000) and repeat a symbol at most three times.
"""

# Value-symbol pairs, largest first, the six subtractive pairs (CM, CD, XC, XL, IX, IV)
# included: a greedy walk over this table yields the standard form directly, with no
# special cases for 4s and 9s.
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

    ``n`` must satisfy ``1 <= n <= 3999``. Subtractive pairs are used for 4s and 9s
    (``4`` -> ``"IV"``, ``1994`` -> ``"MCMXCIV"``, ``3999`` -> ``"MMMCMXCIX"``), so no symbol
    repeats more than three times.

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included, although ``bool``
    is a subclass of ``int``, and a numeric string such as ``"1"`` included) or is outside
    ``1..3999``. The type is checked before the range.
    """
    # ValueError, not TypeError, for a wrong type: the phase-3 rule for int parameters, so
    # the CLI (T2.6) reports every bad argument the same way.
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"to_roman() expects an int, got {type(n).__name__}")
    if not 1 <= n <= 3999:
        raise ValueError(f"to_roman() expects 1 <= n <= 3999, got {n}")
    parts = []
    for value, symbol in _NUMERALS:
        count, n = divmod(n, value)
        parts.append(symbol * count)
    return "".join(parts)
