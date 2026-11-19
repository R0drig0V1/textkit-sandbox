"""Counting helpers: numbers and frequencies computed from a text.

Every public function is listed in the README's function table. Wherever a function here
needs "words", it uses the single word rule of ADR 0001
(docs/decisions/0001-what-counts-as-a-word.md), so that all counts in textkit agree on what a
word is.
"""

import unicodedata

# Characters that join two word runs into one word: the ASCII hyphen-minus, the ASCII
# apostrophe and the typographic apostrophe U+2019 (what most editors type for "don't").
_JOINERS = "-'’"
# Characters that join two runs only between decimal digits ("3.14", "1,000").
_DIGIT_JOINERS = ".,"


def _is_word_char(ch: str) -> bool:
    """Return True for letters, numbers and combining marks (Unicode categories L, N, M).

    Combining marks count so that decomposed (NFD) text such as "cafe\\u0301" stays one word.
    """
    return unicodedata.category(ch)[0] in "LNM"


def _joins(text: str, i: int) -> bool:
    """Return True if ``text[i]`` joins the word run before it to the one after it.

    The caller guarantees that ``text[i - 1]`` is a word character.
    """
    if i + 1 >= len(text) or not _is_word_char(text[i + 1]):
        return False
    ch = text[i]
    if ch in _JOINERS:
        return True
    if ch in _DIGIT_JOINERS:
        return text[i - 1].isdecimal() and text[i + 1].isdecimal()
    return False


def _words(text: str) -> list[str]:
    """Split ``text`` into words following ADR 0001; see ``word_count`` for the rule."""
    words = []
    start = None
    for i, ch in enumerate(text):
        if _is_word_char(ch):
            if start is None:
                start = i
        elif start is not None and not _joins(text, i):
            words.append(text[start:i])
            start = None
    if start is not None:
        words.append(text[start:])
    return words


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a maximal run of letters, digits and combining marks (any script), where a
    single hyphen or apostrophe (``'`` or ``’``) between two such characters joins them
    (``"well-known"``, ``"don't"``: one word each), and a single ``.`` or ``,`` between two
    decimal digits does too (``"3.14"``, ``"1,000"``). Everything else separates words:
    whitespace, other punctuation, symbols and ``_`` (``"snake_case"`` is two words).
    Scripts written without spaces are not segmented (``"日本語"`` is one word). The full
    rule and its case table are in ADR 0001.

    ``""``, whitespace only and punctuation only give 0.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(_words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and per code point:
    no Unicode normalization is applied, so a combining mark in decomposed (NFD) text is a
    key of its own. Characters for which ``str.isspace()`` is true (spaces, tabs, newlines,
    non-breaking spaces and so on) are not counted. Keys appear in order of first occurrence.

    ``""`` and whitespace only give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isspace():
            # dict keeps insertion order (guaranteed since Python 3.7): first occurrence wins.
            counts[ch] = counts.get(ch, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the minutes needed to read ``text`` at ``wpm`` words per minute.

    The result is a whole number of minutes: ``word_count(text) / wpm`` rounded **up**
    (ADR 0004). So a text with no words (``""``, whitespace or punctuation only) takes 0
    minutes, any text with at least one word takes at least 1 minute, and a partial minute
    counts as a full one (201 words at 200 wpm is 2 minutes). Words are counted with
    ``word_count`` (ADR 0001). The arithmetic is integer-only, so there is no float rounding.

    Raises:
        TypeError: if ``text`` is not a ``str``, or ``wpm`` is not an ``int`` (``bool`` is
            rejected too, although it is a subclass of ``int``).
        ValueError: if ``wpm < 1``.
    """
    # bool is checked explicitly: True would otherwise silently mean 1 word per minute.
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"reading_time() expects int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() needs wpm >= 1, got {wpm}")
    # Ceiling division without floats: -(-a // b) == ceil(a / b) for b > 0.
    return -(-word_count(text) // wpm)
