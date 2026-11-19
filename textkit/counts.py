"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in the ADR "What counts as a word"
(docs/decisions/, the ADR titled that way); T1.10 moves `_words` into the shared
tokenizer `textkit/_tokens.py` unchanged.
"""

import unicodedata

# Characters that join two words into one when they sit between word characters:
# "well-known", "don't", "it’s" (U+2019, the typographic apostrophe).
_JOINERS = frozenset("-'’")
# Characters that join only two digits, so that numbers such as "3.14" and "1,000" stay
# one word while "end.Start" and "a,b" are still two.
_NUMBER_JOINERS = frozenset(".,")


def _is_mark(char: str) -> bool:
    """Return True for a combining mark (Unicode category M*), as in NFD "é"."""
    return unicodedata.category(char).startswith("M")


def _words(text: str) -> list[str]:
    """Split `text` into words following the ADR "What counts as a word".

    A word is a maximal run of alphanumeric characters (`str.isalnum`, so any script),
    plus combining marks that follow one of them, where a single `-`, `'` or `’` between
    two such characters, or a single `.` or `,` between two digits, joins both sides into
    one word. Everything else separates words and is not part of any word.
    """
    words: list[str] = []
    current: list[str] = []
    last = len(text) - 1
    for i, char in enumerate(text):
        if char.isalnum() or (current and _is_mark(char)):
            current.append(char)
            continue
        if current and i < last and text[i + 1].isalnum():
            if char in _JOINERS:
                current.append(char)
                continue
            # The previous character may be a mark ("é"), which is not a digit,
            # so a number joiner after a mark separates, as it does after a letter.
            if char in _NUMBER_JOINERS and current[-1].isdigit() and text[i + 1].isdigit():
                current.append(char)
                continue
        if current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))
    return words


def word_count(text: str) -> int:
    """Return the number of words in `text`.

    What counts as a word is decided in the ADR "What counts as a word" (docs/decisions/),
    which ends with the table of cases that tests/test_counts.py checks row by row. In
    short: runs of letters and digits in any script; a single hyphen or apostrophe inside
    a word keeps it whole ("well-known", "don't"); a single "." or "," between digits keeps
    a number whole ("3.14", "1,000"); punctuation and whitespace alone are not words.

    `""`, whitespace-only and punctuation-only text give 0. Raises `TypeError` when `text`
    is not a `str` (iterating bytes or a list would silently give a wrong count).
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects a str, got {type(text).__name__}")
    return len(_words(text))
