"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is fixed by ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md);
T1.10 moves it into the shared tokenizer ``textkit/_tokens.py`` unchanged.
"""

import unicodedata

# Characters that join two word parts into one word ("well-known", "don't", "don’t").
_JOINERS = frozenset("-'’")
# Characters that join two runs of decimal digits into one number ("3.14", "1,000").
_DIGIT_JOINERS = frozenset(".,")


def _is_mark(ch: str) -> bool:
    """True for combining marks (Unicode category M*), which continue a word but never start one."""
    return unicodedata.category(ch).startswith("M")


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following ADR 0002.

    A word starts with a letter or digit (``str.isalnum()``) and continues through letters,
    digits and combining marks. One ``-``, ``'`` or ``’`` between a word character and a
    letter or digit keeps the word going (``"well-known"``, ``"don't"``), and so does one
    ``.`` or ``,`` between two decimal digits (``"3.14"``, ``"1,000"``). Every other
    character (whitespace, other punctuation, symbols, ``_``, dashes) separates words.
    ``""`` and text with no letters or digits give 0.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    count = 0
    in_word = False
    n = len(text)
    for i, ch in enumerate(text):
        if ch.isalnum():
            if not in_word:
                count += 1
                in_word = True
        elif in_word and _is_mark(ch):
            pass  # a combining mark continues the word (NFD "ú" is one letter)
        elif in_word and i + 1 < n and text[i + 1].isalnum() and (
            ch in _JOINERS
            or (ch in _DIGIT_JOINERS and text[i - 1].isdecimal() and text[i + 1].isdecimal())
        ):
            pass  # a single joiner inside a word; the next character resumes it
        else:
            in_word = False
    return count


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is per code point and case-sensitive (``"a"`` and ``"A"`` are separate keys).
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break spaces
    and other Unicode whitespace) are not counted. Keys appear in order of first occurrence.
    No Unicode normalization is applied, so a decomposed ``"ú"`` counts as ``"u"`` plus the
    combining mark U+0301. ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    # A plain dict keeps insertion order (Python 3.7+), which gives first-occurrence order;
    # collections.Counter would too, but returning a plain dict keeps the documented type.
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isspace():
            counts[ch] = counts.get(ch, 0) + 1
    return counts
