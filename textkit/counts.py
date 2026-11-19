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
