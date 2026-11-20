"""Shared tokenizer: the prose word rule of ADR 0002, as a private helper module.

The rule is decided in docs/decisions/0002-word-count-what-counts-as-a-word.md; change that
ADR (and its case table) before changing the pattern below. ``textkit.counts.word_count`` is
``len(words(text))``. The module name starts with ``_``, so it holds no public functions:
``scripts/check.sh`` skips it and it has no README row or CHANGELOG line.

``textkit.cases.to_snake_case`` deliberately does not use this rule: identifiers split at case
changes and at every hyphen, which prose words do not (ADR 0001).
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
    # Every group is non-capturing, so findall() returns whole matches.
    run = rf"(?:[^\W_][{marks}]*)+"
    return re.compile(rf"{run}(?:(?:[-'’]|(?<=\d)[.,](?=\d)){run})*")


def words(text: str) -> list[str]:
    """Return the words of ``text`` in order, each exactly as it appears in the input.

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
    return _word_pattern().findall(text)
