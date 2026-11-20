"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in docs/decisions/0002-word-count-what-counts-as-a-word.md
and implemented once, in ``textkit._tokens.words``; change that ADR (and its case table)
before changing the pattern there.
"""

from textkit._tokens import words


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a maximal run of letters or digits (any script), each optionally followed by
    combining marks, so NFC and NFD forms of the same text count the same. A single hyphen
    (``"well-known"``), a single apostrophe, ASCII or typographic (``"don't"``,
    ``"don’t"``), or a ``.``/``,`` between two digits (``"3.14"``, ``"1,000"``) joins two
    runs into one word. Whitespace, other punctuation, ``_`` and doubled joiners
    (``"rock--roll"``) separate words; apostrophes and hyphens at the edges of a word are
    not part of it, and a combining mark with no letter or digit before it is not a word.
    ``""``, whitespace only and punctuation only give ``0``. The first call builds the
    pattern (about 0.1 s); later calls reuse it.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included).
    """
    # Checked here as well as in words() so the error names the public function.
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and works on code
    points: no Unicode normalization is applied, so a combining mark is counted as its own
    character. Every character for which ``str.isspace()`` is true (spaces, tabs, newlines,
    non-breaking and other Unicode spaces) is skipped. Keys appear in the order of their first
    occurrence. ``""`` and whitespace-only input give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), like ``word_count``.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    # A plain dict keeps insertion order (Python 3.7+), which gives first-occurrence order
    # for free; collections.Counter would too, but the contract is a plain dict.
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isspace():
            counts[ch] = counts.get(ch, 0) + 1
    return counts
