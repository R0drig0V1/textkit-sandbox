"""Shared tokenizer (private: no README row, no CHANGELOG line; see docs/architecture.md).

``words(text)`` implements the word rule of ADR 0002
(docs/decisions/0002-what-counts-as-a-word.md) exactly, so every helper that needs "the
words of a text" splits it the same way. ``word_count`` is ``len(words(text))``;
``to_snake_case`` uses it only where ADR 0001's identifier rule agrees with it.
"""

import unicodedata

# Characters that join two word parts into one word ("well-known", "don't", "don’t").
_JOINERS = frozenset("-'’")
# Characters that join two runs of decimal digits into one number ("3.14", "1,000").
_DIGIT_JOINERS = frozenset(".,")


def _is_mark(ch: str) -> bool:
    """True for combining marks (Unicode category M*), which continue a word but never start one."""
    return unicodedata.category(ch).startswith("M")


def words(text: str) -> list[str]:
    """Return the words of ``text``, in order, as defined by ADR 0002.

    A word starts with a letter or digit (``str.isalnum()``) and continues through letters,
    digits and combining marks. One ``-``, ``'`` or ``’`` between a word character and a
    letter or digit keeps the word going (``"well-known"``, ``"don't"``), and so does one
    ``.`` or ``,`` between two decimal digits (``"3.14"``, ``"1,000"``). Every other
    character (whitespace, other punctuation, symbols, ``_``, dashes) separates words and
    is not part of any word. Each word is a substring of ``text``, unchanged (no case
    folding, no normalization). ``""`` and text with no letters or digits give ``[]``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    result = []
    start = -1  # index where the current word began; -1 when not inside a word
    n = len(text)
    for i, ch in enumerate(text):
        if ch.isalnum():
            if start < 0:
                start = i
        elif start >= 0 and _is_mark(ch):
            pass  # a combining mark continues the word (NFD "ú" is one letter)
        elif start >= 0 and i + 1 < n and text[i + 1].isalnum() and (
            ch in _JOINERS
            or (ch in _DIGIT_JOINERS and text[i - 1].isdecimal() and text[i + 1].isdecimal())
        ):
            # A single joiner inside a word; the next character resumes it. Requiring a word
            # character right after it is what makes a doubled joiner ("a--b") or a trailing
            # one ("students'") separate instead.
            pass
        elif start >= 0:
            result.append(text[start:i])
            start = -1
    if start >= 0:
        result.append(text[start:])
    return result
