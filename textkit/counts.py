"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is the one in docs/decisions/0002-what-counts-as-a-word.md; the
shared tokenizer `textkit._tokens.words` implements it and is the single place that rule
lives in code.
`char_freq` counts characters, not words, so that rule does not apply to it.
"""

from textkit import _tokens


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
    return len(_tokens.words(text))


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


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read `text` at `wpm` words per minute.

    Words are counted with `word_count` (the word rule of ADR 0002). The result is the
    number of words divided by `wpm`, rounded **up** to a whole minute (ADR 0004): text with
    no words (`""`, whitespace or punctuation only) takes 0 minutes, and any text with at
    least one word takes at least 1 minute, however high `wpm` is. The division is done in
    integers, so the result is exact for any word count.

    Raises:
        TypeError: if `text` is not a `str`, or `wpm` is not an `int` (`bool` included).
        ValueError: if `wpm < 1`.
    """
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects str, got {type(text).__name__}")
    # bool is a subclass of int; reading_time(text, True) is a mistake, not "1 wpm". A float
    # would make the integer ceiling below return a float.
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, got {wpm}")
    # Ceiling division without floats: -(-a // b) == ceil(a / b) for b > 0.
    return -(-word_count(text) // wpm)
