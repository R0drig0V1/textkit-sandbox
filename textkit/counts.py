"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is fixed by ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md);
T1.10 moves it into the shared tokenizer ``textkit/_tokens.py`` unchanged. ``reading_time``
rounds its word count up to whole minutes, by ADR 0004
(docs/decisions/0004-reading-time-rounds-up.md).
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


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read ``text`` at ``wpm`` words per minute (ADR 0004).

    The word count comes from ``word_count`` (ADR 0002) and is rounded **up** to whole
    minutes: ``ceil(word_count(text) / wpm)``. So a text with no words (``""``, whitespace,
    punctuation only) gives 0, any text with at least one word gives at least 1 (under one
    minute reads as 1), and exactly ``wpm`` words give 1 while ``wpm + 1`` give 2.

    Raises:
        TypeError: if ``text`` is not a ``str``, or ``wpm`` is not an ``int`` (``bool`` and
            ``float`` are rejected).
        ValueError: if ``wpm`` is less than 1.
    """
    # bool is a subclass of int; reading_time(text, True) is a bug, not a speed of 1.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"wpm must be an int, not {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, not {wpm}")
    words = word_count(text)
    # Integer ceiling division: exact for any size, no float rounding (ADR 0004).
    return -(-words // wpm)
