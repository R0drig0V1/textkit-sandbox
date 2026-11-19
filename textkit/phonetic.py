"""Phonetic codes for names (plan task T3.7, docs/phases/phase-3-converters.md).

``soundex`` is the American Soundex code. Soundex has several published variants that agree
on common names such as ``Robert`` (R163) but differ on others; the plan pins one of them
(H and W are transparent between letters of the same code, the first letter takes part in
de-duplication, non-letters are removed before coding), and ``Ashcraft`` (A261), ``Pfister``
(P236) and ``Tymczak`` (T522) are the names that tell the variants apart. Every public
function is listed in the README's function table.
"""

import string

# Soundex digit of each coded letter. Letters missing here (A E I O U Y H W) are not coded.
_CODES = {
    **dict.fromkeys("BFPV", "1"),
    **dict.fromkeys("CGJKQSXZ", "2"),
    **dict.fromkeys("DT", "3"),
    "L": "4",
    **dict.fromkeys("MN", "5"),
    "R": "6",
}
# Not coded and transparent: the same code on both sides of these is coded once.
_TRANSPARENT = frozenset("HW")
# Explicit ASCII set, not str.isalpha (which accepts "é") and not a test after upper-casing
# ("ß".upper() is "SS", and the Kelvin sign U+212A lower-cases to "k").
_ASCII_LETTERS = frozenset(string.ascii_letters)


def soundex(name: str) -> str:
    """Return the American Soundex code of ``name``: a letter and three digits (``"R163"``).

    Steps, in order:

    1. Every character that is not an ASCII letter is removed. It is transparent, not a
       separator, so ``"O'Brien"`` is coded as ``"OBRIEN"`` and ``"José"`` as ``"JOS"``
       (no Unicode normalization: NFD ``"José"`` keeps its base ``e`` and gives the same
       code). Case is ignored.
    2. The first letter is kept, upper-cased.
    3. The other letters are coded B F P V -> 1, C G J K Q S X Z -> 2, D T -> 3, L -> 4,
       M N -> 5, R -> 6; A E I O U Y H W get no digit.
    4. Letters with the same code that are adjacent, or separated only by H or W, are coded
       once, the first letter included (``"Pfister"`` -> ``"P236"``, ``"Ashcraft"`` ->
       ``"A261"``). The same code separated by a vowel (A E I O U Y) is coded twice
       (``"Tymczak"`` -> ``"T522"``).
    5. The result is padded with ``0`` or cut to 4 characters (``"Lee"`` -> ``"L000"``).

    Raises ``ValueError`` if ``name`` contains no ASCII letter (``""``, ``"123"``, ``"é"``)
    and ``TypeError`` if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"soundex() expects a str, got {type(name).__name__}")
    letters = [char.upper() for char in name if char in _ASCII_LETTERS]
    if not letters:
        raise ValueError(f"soundex() needs at least one ASCII letter, got {name!r}")

    first = letters[0]
    digits = []
    # The code of the last coded letter still "in effect": a vowel resets it, H and W leave
    # it alone. Starting from the first letter's code makes it part of the de-duplication.
    previous = _CODES.get(first)
    for letter in letters[1:]:
        if letter in _TRANSPARENT:
            continue
        code = _CODES.get(letter)
        if code is not None and code != previous:
            digits.append(code)
        previous = code  # None for a vowel, so the same code after it is coded again.
    return (first + "".join(digits) + "000")[:4]
