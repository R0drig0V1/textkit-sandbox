"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in docs/decisions/0002-word-count-what-counts-as-a-word.md;
change that ADR (and its case table) before changing the pattern below.
"""

import functools
import re
import sys
import unicodedata


@functools.lru_cache(maxsize=None)
def _word_pattern() -> "re.Pattern[str]":
    """Compile the word pattern of ADR 0002 (once, on first use).

    Python's ``\\w`` does not match combining marks (Unicode category M: Mn, Mc, Me), so
    decomposed text such as NFD ``"cafe\\u0301"`` or Devanagari vowel signs would split
    words. ``re`` has no ``\\p{M}``, so the mark class is generated from ``unicodedata``
    instead of hand-written ranges, which would go stale. Generating it scans every code
    point (~0.1 s), hence the lazy, cached compile rather than doing it at import.
    """
    ranges = []
    for cp in range(sys.maxunicode + 1):
        if unicodedata.category(chr(cp))[0] == "M":
            if ranges and ranges[-1][1] == cp - 1:
                ranges[-1][1] = cp
            else:
                ranges.append([cp, cp])
    marks = "".join(f"\\U{a:08x}-\\U{b:08x}" for a, b in ranges)
    # A run is letters/digits ([^\W_]: Unicode word characters minus "_"), each optionally
    # followed by combining marks; a mark never starts a run. Runs join into one word across
    # a single hyphen, a single apostrophe (ASCII or U+2019), or a "." / "," between two
    # digits (so "3.14" and "1,000" stay one number). Everything else, "_" included, separates.
    run = rf"(?:[^\W_][{marks}]*)+"
    return re.compile(rf"{run}(?:(?:[-'’]|(?<=\d)[.,](?=\d)){run})*")


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
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return sum(1 for _ in _word_pattern().finditer(text))


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
