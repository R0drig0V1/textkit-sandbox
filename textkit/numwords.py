"""Spelling numbers out in English words. Every public function is listed in the README's
function table.

The module is ``numwords`` and not ``numbers``: a ``textkit/numbers.py`` would shadow the
standard library's ``numbers`` module whenever ``textkit/`` itself is on ``sys.path`` (plan
task T3.4, docs/phases/phase-3-converters.md).
"""

_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen",
]
# Indexed by the tens digit; 0 and 1 are never used (below 20 comes from _ONES).
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _below_hundred(n: int) -> str:
    """Spell ``0 <= n <= 99``, with a hyphen between the tens and a non-zero unit."""
    if n < 20:
        return _ONES[n]
    tens, unit = divmod(n, 10)
    return _TENS[tens] if unit == 0 else f"{_TENS[tens]}-{_ONES[unit]}"


def number_to_words(n: int) -> str:
    """Return ``n`` spelled out in English words, for ``0 <= n <= 999``.

    The result is lower case, the tens are hyphenated with their unit and there is no
    "and" after "hundred" (the American style): ``0`` -> ``"zero"``, ``13`` ->
    ``"thirteen"``, ``20`` -> ``"twenty"``, ``42`` -> ``"forty-two"``, ``100`` ->
    ``"one hundred"``, ``105`` -> ``"one hundred five"``, ``110`` -> ``"one hundred ten"``,
    ``999`` -> ``"nine hundred ninety-nine"``.

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included, although it is a
    subclass of ``int``) or is outside ``0..999``. The type is checked before the range, so
    no other exception escapes whatever the argument is.
    """
    # bool is checked explicitly: True would otherwise be spelled "one".
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"number_to_words() expects an int, got {type(n).__name__}")
    if not 0 <= n <= 999:
        raise ValueError(f"number_to_words() expects 0 <= n <= 999, got {n}")
    hundreds, rest = divmod(n, 100)
    if hundreds == 0:
        return _below_hundred(rest)
    head = f"{_ONES[hundreds]} hundred"
    return head if rest == 0 else f"{head} {_below_hundred(rest)}"
