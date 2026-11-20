"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in docs/decisions/0001-word-count-what-counts-as-a-word.md;
change that ADR (and its case table) before changing the pattern below.
"""

import re

# A word is a run of letters/digits ([^\W_]: Unicode word characters minus "_"), where the
# runs may be joined into one word by a single hyphen, a single apostrophe (ASCII or U+2019),
# or a "." / "," that sits between two digits (so "3.14" and "1,000" stay one number).
# Everything else, "_" included, separates words. See ADR 0001 for the reasoning.
_WORD = re.compile(r"[^\W_]+(?:(?:[-'’]|(?<=\d)[.,](?=\d))[^\W_]+)*")


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a maximal run of letters or digits (any script), where a single hyphen
    (``"well-known"``), a single apostrophe, ASCII or typographic (``"don't"``,
    ``"don’t"``), or a ``.``/``,`` between two digits (``"3.14"``, ``"1,000"``) joins two
    runs into one word. Whitespace, other punctuation, ``_`` and doubled joiners
    (``"rock--roll"``) separate words; apostrophes and hyphens at the edges of a word are
    not part of it. ``""``, whitespace only and punctuation only give ``0``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return sum(1 for _ in _WORD.finditer(text))
