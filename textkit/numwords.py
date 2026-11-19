"""English words for small whole numbers. The module is named ``numwords`` and not
``numbers`` because a ``numbers.py`` would shadow the standard library's ``numbers`` module
whenever ``textkit/`` itself is on ``sys.path``. Every public function is listed in the
README's function table."""

# Words for 0..19, indexed by value: below twenty English has no regular pattern.
_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen",
)

# Words for the multiples of ten, indexed by the tens digit; 0 and 1 are covered by _ONES.
_TENS = (
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
)


def _below_hundred(n: int) -> str:
    """Words for ``0 <= n <= 99``: a single word below twenty, else hyphenated tens."""
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] if ones == 0 else f"{_TENS[tens]}-{_ONES[ones]}"


def number_to_words(n: int) -> str:
    """Return ``n`` written out in English words.

    The result is lower case, the tens are hyphenated and no "and" is used:
    ``0`` -> ``"zero"``, ``42`` -> ``"forty-two"``, ``105`` -> ``"one hundred five"``,
    ``999`` -> ``"nine hundred ninety-nine"``.

    Raises:
        ValueError: if ``n`` is not an ``int`` (a ``bool`` included, although ``bool`` is a
            subclass of ``int``) or is outside ``0 <= n <= 999``. The type is checked
            before the range.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"number_to_words expects an int, got {type(n).__name__}")
    if not 0 <= n <= 999:
        raise ValueError(f"number_to_words supports 0 to 999, got {n}")
    hundreds, rest = divmod(n, 100)
    if hundreds == 0:
        return _below_hundred(rest)
    words = f"{_ONES[hundreds]} hundred"
    return words if rest == 0 else f"{words} {_below_hundred(rest)}"
