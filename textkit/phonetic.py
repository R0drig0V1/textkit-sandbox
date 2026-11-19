"""Phonetic codes for names. Every public function is listed in the README's function table."""

# American Soundex digit for each coded letter. A E I O U Y H W are deliberately absent: they
# get no digit, but they still matter for collapsing (see soundex).
_SOUNDEX_CODES = {
    **dict.fromkeys("BFPV", "1"),
    **dict.fromkeys("CGJKQSXZ", "2"),
    **dict.fromkeys("DT", "3"),
    "L": "4",
    **dict.fromkeys("MN", "5"),
    "R": "6",
}
_SOUNDEX_VOWELS = frozenset("AEIOUY")


def soundex(name: str) -> str:
    """Return the four-character American Soundex code of ``name``.

    Every character that is not an ASCII letter is removed first; it is transparent, not a
    separator, so ``"O'Brien"`` is coded as ``"OBRIEN"`` and ``"José"`` as ``"JOS"``. Case is
    ignored. The first letter is kept, upper-cased; the remaining letters are coded
    B F P V -> 1, C G J K Q S X Z -> 2, D T -> 3, L -> 4, M N -> 5, R -> 6, and
    A E I O U Y H W get no digit. Letters with the same digit that are adjacent, or separated
    only by H or W, are coded once (the first letter counts as coded); the same digit
    separated by a vowel (A E I O U Y) is coded twice. The result is padded with ``0`` or cut
    to four characters.

    Examples: ``soundex("Robert") == "R163"``, ``soundex("Ashcraft") == "A261"``,
    ``soundex("Lee") == "L000"``.

    Raises:
        ValueError: ``name`` contains no ASCII letter (``""``, ``"123"``, ``"é"``).
    """
    letters = [c.upper() for c in name if c.isascii() and c.isalpha()]
    if not letters:
        raise ValueError(f"soundex needs at least one ASCII letter: {name!r}")
    first = letters[0]
    code = first
    # The digit of the last coded letter; the first letter counts, so "Pfister" skips the F.
    previous = _SOUNDEX_CODES.get(first)
    for letter in letters[1:]:
        if len(code) == 4:
            break
        if letter in _SOUNDEX_VOWELS:
            # A vowel separates equal digits, so the next one is coded again (Tymczak).
            previous = None
            continue
        digit = _SOUNDEX_CODES.get(letter)
        if digit is None:
            # H or W: transparent, keeps `previous` so equal digits around it collapse.
            continue
        if digit != previous:
            code += digit
        previous = digit
    return code.ljust(4, "0")
