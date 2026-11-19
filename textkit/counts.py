"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0001-word-rule.md and implemented once, in
the shared tokenizer ``textkit._tokens.words`` (plan task T1.10); ``word_count`` only counts
what it returns, so later helpers that need words reuse the same rule without re-deciding it.
How ``reading_time`` rounds a word count to whole minutes is decided in
docs/decisions/0004-reading-time-rounding.md.
"""

from textkit._tokens import words

# Kept under its old name because tests/test_counts.py (which T1.10 must not modify) imports
# ``_words`` from here to check ADR 0001's Words column.
_words = words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following the word rule of ADR 0001.

    A word is a run of letters and digits (``str.isalnum()``, so any script counts), with
    combining marks kept inside it and joined across one ``-``, ``'`` or ``\\u2019`` between
    two letters or digits (``"well-known"``, ``"don't"``: one word each), or across one ``.``
    or ``,`` between two decimal digits (``"3.14"``, ``"1,000"``: one word each). Everything
    else separates words: whitespace, other punctuation, ``_``, symbols, emoji. So ``""``,
    whitespace only and punctuation only all give 0. Scripts written without spaces (Chinese,
    Japanese, Thai) count each unbroken run as one word.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), rather than counting
            the elements of some other iterable.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are separate keys) and per code point:
    no Unicode normalization is applied, so a combining mark in NFD input is its own key.
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break
    spaces, ...) are skipped. Keys appear in the order of their first occurrence, which a
    plain ``dict`` keeps (Python 3.7+). ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), as ``word_count`` does,
            rather than counting the elements of some other iterable.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the estimated reading time of ``text`` in whole minutes, rounded up.

    The estimate is ``word_count(text)`` (the word rule of ADR 0001) divided by ``wpm``,
    words per minute, rounded up to a whole minute as decided in ADR 0004: a text with no
    words (``""``, whitespace or punctuation only) gives 0, any text with at least one word
    gives at least 1, and exactly ``k * wpm`` words give ``k``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), or if ``wpm`` is not
            an ``int`` (``float`` and ``bool`` included).
        ValueError: if ``wpm`` is less than 1.
    """
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects str, got {type(text).__name__}")
    # bool is a subclass of int, but wpm=True is a caller's mistake, not a speed of 1.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"reading_time() wpm must be int, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() wpm must be at least 1, got {wpm}")
    # Ceiling division in integers: exact for any count, unlike math.ceil(words / wpm).
    return -(-word_count(text) // wpm)
