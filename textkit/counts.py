"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in docs/decisions/0002-word-count-what-counts-as-a-word.md
and implemented once, in ``textkit._tokens.words``; change that ADR (and its case table)
before changing the pattern there. The rounding of ``reading_time`` is decided in
docs/decisions/0004-reading-time-rounding.md.
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


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read ``text`` at ``wpm`` words per minute.

    Words are counted with ``word_count`` (ADR 0002). The result is rounded **up**
    (ADR 0004): ``""`` and text with no words give ``0``; any text with at least one word
    gives at least ``1``, so text under one minute reads as one minute; ``wpm + 1`` words give
    ``2``. The arithmetic is on integers, so there is no floating-point rounding.

    Raises:
        ValueError: if ``wpm < 1``, checked before ``text`` is read (even for ``""``).
        TypeError: if ``wpm`` is not an ``int`` (``bool`` and ``float`` included), or if
            ``text`` is not a ``str`` (raised by ``word_count``).
    """
    # bool is a subclass of int, but reading_time("x", True) is a bug, not a speed of 1.
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, got {wpm}")
    # Ceiling division without floats: -(-a // b) == ceil(a / b) for integers, and 0 for a == 0.
    return -(-word_count(text) // wpm)
