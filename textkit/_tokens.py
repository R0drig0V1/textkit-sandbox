"""Shared tokenizer: the prose word rule of ADR 0002, as a private helper module.

The rule is decided in docs/decisions/0002-word-count-what-counts-as-a-word.md; change that
ADR (and its case table) before changing the pattern below. ``words`` returns ``Token``s, each
word with its code-point offsets in the input (ADR 0002, "Offsets"), so callers that need
positions (diffs, n-grams) do not search for the word again. ``textkit.counts.word_count`` is
``len(words(text))``. The module name starts with ``_``, so it holds no public functions:
``scripts/check.sh`` skips it and it has no README row or CHANGELOG line.

``textkit.cases.to_snake_case`` deliberately does not use this rule: identifiers split at case
changes and at every hyphen, which prose words do not (ADR 0001).
"""

import functools
import re
import sys
import unicodedata
from typing import NamedTuple


class Token(NamedTuple):
    """One word of ``words``: its text and where it is in the input.

    ``start`` and ``end`` are code-point offsets (``str`` indices, not bytes or UTF-16 units),
    ``end`` exclusive, so ``text_argument[token.start:token.end] == token.text`` always.
    """

    text: str
    start: int
    end: int


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
    # Every group is non-capturing, so group() is the whole word.
    run = rf"(?:[^\W_][{marks}]*)+"
    return re.compile(rf"{run}(?:(?:[-'’]|(?<=\d)[.,](?=\d)){run})*")


def words(text: str) -> list[Token]:
    """Return the words of ``text`` in order, as ``Token(text, start, end)``.

    Each token's ``text`` is the word exactly as it appears in the input, and
    ``text[token.start:token.end] == token.text``. Offsets count code points (a character
    outside the BMP is one), come from the match itself and are strictly increasing; tokens
    never overlap. Combining marks stay inside their word, so NFD ``"cafe\\u0301"`` is one
    token of length 5.

    A word is a maximal run of letters or digits (any script), each optionally followed by
    combining marks; a single hyphen, a single apostrophe (``'`` or ``’``) or a ``.``/``,``
    between two digits joins two runs into one word (``"well-known"``, ``"don't"``,
    ``"3.14"``). Whitespace, other punctuation, ``_`` and doubled joiners separate words and
    are not returned. Nothing is normalized or case-folded. ``""``, whitespace only and
    punctuation only give ``[]``. The first call builds the pattern (about 0.1 s).

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"words() expects str, got {type(text).__name__}")
    # Offsets come from each match, never from searching for the word in ``text``: a search
    # would find the first occurrence of a repeated word, not this one.
    return [Token(m.group(), m.start(), m.end()) for m in _word_pattern().finditer(text)]
