"""Counting helpers. Every public function is listed in the README's function table.

The word rule is the word-rule ADR, docs/decisions/0002-what-counts-as-a-word.md.
"""

import unicodedata

# Joiners that keep a word together when a word character is on both sides (word-rule ADR, rule 2).
_JOINERS = frozenset("-'’")
# Joiners only between two decimal digits, so "3.14" and "1,000" are one word.
_DIGIT_JOINERS = frozenset(".,")


def _is_mark(char: str) -> bool:
    """True for a combining mark (Unicode category M*), which extends the word before it."""
    return unicodedata.category(char).startswith("M")


def _word_spans(text: str) -> list[tuple[int, int]]:
    """Return the (start, end) index pairs of the words of ``text`` under the word-rule ADR.

    A hand-written scanner rather than a regex: ``re`` has no class for combining marks and
    the digit-only joiners need to look at both neighbours.
    """
    spans = []
    i, n = 0, len(text)
    while i < n:
        if not text[i].isalnum():
            # Separators, and combining marks with no word character before them.
            i += 1
            continue
        start = i
        i += 1
        while i < n:
            char = text[i]
            if char.isalnum() or _is_mark(char):
                i += 1
                continue
            # A joiner needs a word character right after it; the one before it is text[i - 1]
            # (a letter, digit or mark, since we are inside a word).
            if i + 1 < n and text[i + 1].isalnum():
                if char in _JOINERS:
                    i += 2
                    continue
                if char in _DIGIT_JOINERS and text[i - 1].isdecimal() and text[i + 1].isdecimal():
                    i += 2
                    continue
            break
        spans.append((start, i))
    return spans


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a run of letters and digits (``str.isalnum``, so any script), with combining
    marks kept in the word they follow; a hyphen or an apostrophe (``'`` or ``’``) between
    two such characters joins them (``"well-known"``, ``"don't"`` are one word), and so does
    ``.`` or ``,`` between two digits (``"3.14"``, ``"1,000"``). Everything else, the
    underscore and dashes included, separates words. Empty, whitespace-only and
    punctuation-only text gives 0. The full rule and its case table are in
    docs/decisions/0002-what-counts-as-a-word.md.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects a str, got {type(text).__name__}")
    return len(_word_spans(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and per code point,
    with no Unicode normalization, so a combining mark counts as a character of its own.
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break spaces
    and the other Unicode whitespace) are not counted. Keys appear in order of first
    occurrence. Empty or whitespace-only text gives ``{}``.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects a str, got {type(text).__name__}")
    # A plain dict keeps insertion order (guaranteed since Python 3.7), which is exactly
    # first-occurrence order; collections.Counter would too, but the contract is a dict.
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts
