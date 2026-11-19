"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in the ADR "What counts as a word"
(docs/decisions/0001-what-counts-as-a-word.md) and implemented once, in the shared
tokenizer `textkit._tokens.words`.
"""

from textkit._tokens import words


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
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in `text`.

    Counting is case-sensitive (`"a"` and `"A"` are separate keys) and per code point, with
    no Unicode normalization, so NFC "é" is one key while NFD "é" counts "e" and the
    combining accent separately. Characters for which `str.isspace()` is true (spaces, tabs,
    newlines, U+00A0 and the other Unicode spaces) are not counted. Keys appear in order of
    first occurrence, which a plain `dict` guarantees on Python 3.7+.

    `""` and whitespace-only text give `{}`. Raises `TypeError` when `text` is not a `str`
    (iterating bytes would count integers, a list would count its items).
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects a str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the minutes needed to read `text` at `wpm` words per minute, rounded up.

    Words are counted with `word_count`. Rounding is decided in the ADR "Reading time
    rounding" (docs/decisions/): the result is `ceil(word_count(text) / wpm)`, so text
    with no words gives 0 and any text with at least one word gives at least 1 (a
    15-word note is a 1-minute read, never 0).

    Raises `TypeError` when `text` is not a `str` or `wpm` is not an `int` (`bool` is
    rejected too: `reading_time(text, True)` is a bug, not 1 wpm), and `ValueError` when
    `wpm < 1`. `wpm` is checked before `text` is counted.
    """
    # bool is a subclass of int, so it has to be excluded explicitly.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() needs wpm >= 1, got {wpm}")
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects a str, got {type(text).__name__}")
    # Integer ceiling division: exact for any word count, unlike math.ceil on a float.
    return -(-word_count(text) // wpm)
