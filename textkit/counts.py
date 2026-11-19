"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is the one in docs/decisions/0002-what-counts-as-a-word.md; the
private `_words` tokenizer implements it and is the single place that rule lives in code.
`char_freq` counts characters, not words, so that rule does not apply to it.
"""

import unicodedata

# Characters that join two parts into one word when they sit between a word character and
# an alphanumeric one ("well-known", "don't", "don’t"). U+2010 is the Unicode hyphen; U+2019
# is the typographic apostrophe that word processors substitute for "'".
_HYPHENS = frozenset("-‐")
_APOSTROPHES = frozenset("'’")
# Characters that join two parts only between two decimal digits ("3.14", "1,000"), so that
# a number is one word but "end.Next" or "a,b" are still two.
_DIGIT_SEPARATORS = frozenset(".,")


def _joins(prev: str, char: str, nxt: str) -> bool:
    """Whether `char`, inside a word after `prev` and before `nxt`, keeps the word going."""
    if char in _HYPHENS or char in _APOSTROPHES:
        return nxt.isalnum()
    if char in _DIGIT_SEPARATORS:
        return prev.isdecimal() and nxt.isdecimal()
    return False


def _words(text: str) -> list[str]:
    """Split `text` into words by the rule of ADR 0002 (see the module docstring).

    A word starts at an alphanumeric character (`str.isalnum`) and continues over
    alphanumeric characters, combining marks (so NFD input counts like NFC input) and the
    joiners accepted by `_joins`. Any other character ends the current word.
    """
    words: list[str] = []
    current: list[str] = []
    last = len(text) - 1
    for i, char in enumerate(text):
        if char.isalnum():
            current.append(char)
        elif current and unicodedata.category(char).startswith("M"):
            # A combining mark extends a word but never starts one.
            current.append(char)
        elif current and i < last and _joins(text[i - 1], char, text[i + 1]):
            current.append(char)
        elif current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))
    return words


def word_count(text: str) -> int:
    """Return the number of words in `text`.

    A word is a maximal run of alphanumeric characters (Unicode-aware, `str.isalnum`), plus
    any combining marks that follow them. A hyphen (`-`, U+2010) or apostrophe (`'`, U+2019)
    between a word character and an alphanumeric character joins both sides into one word
    ("well-known", "don't"); `.` or `,` between two decimal digits does the same ("3.14",
    "1,000,000"). Everything else separates words: whitespace, other punctuation, `_`,
    symbols and emoji. There is no dictionary or language-specific segmentation, so a run
    of CJK characters with no separator is one word. The full rule and its table of cases
    are in ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md).

    Returns 0 for an empty string or text with no alphanumeric character.

    Raises:
        TypeError: if `text` is not a `str`.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(_words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in `text`.

    Counting is case-sensitive (`"a"` and `"A"` are different keys) and per code point: no
    Unicode normalization is applied, so a combining mark in NFD text is a key of its own.
    Characters for which `str.isspace()` is true (spaces, tabs, newlines, no-break and other
    Unicode spaces) are not counted. Keys appear in the order of their first occurrence in
    `text`. The result is a new plain `dict`; it is empty for `""` or whitespace-only text.

    Raises:
        TypeError: if `text` is not a `str`.
    """
    if not isinstance(text, str):
        # Without this, a list or bytes would be iterated and counted silently.
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    # A plain dict keeps insertion order (Python 3.7+), which is the first-occurrence order.
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts
