"""Shared tokenizer: the single implementation of textkit's word rule (plan task T1.10).

The rule is docs/decisions/0002-what-counts-as-a-word.md. ``words`` is the only place it is
implemented; ``textkit.counts.word_count`` is ``len(words(text))``. The module name starts
with ``_`` so that it is private: it has no README row or CHANGELOG line, and
``scripts/check.sh`` does not treat its functions as public.

``textkit.cases.to_snake_case`` does not use it: that ADR splits identifiers, not prose, and
docs/decisions/0003-snake-case-capital-runs.md keeps characters this rule drops.
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
            # (a letter, digit or mark, since we are inside a word). A joiner followed by
            # another joiner fails this test, so "a--b" ends the word before the first "-".
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


def words(text: str) -> list[str]:
    """Return the words of ``text``, in order, as substrings of it (nothing is normalized).

    A word is a run of letters and digits (``str.isalnum``, so any script), with combining
    marks kept in the word they follow; a hyphen or an apostrophe (``'`` or ``’``) between
    two such characters joins them (``"well-known"``, ``"don't"``), and so does ``.`` or
    ``,`` between two digits (``"3.14"``, ``"1,000"``). Everything else, the underscore and
    dashes included, separates words and is not returned. Empty, whitespace-only and
    punctuation-only text gives ``[]``. The full rule and its case table are in
    docs/decisions/0002-what-counts-as-a-word.md.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"words() expects a str, got {type(text).__name__}")
    return [text[start:end] for start, end in _word_spans(text)]
