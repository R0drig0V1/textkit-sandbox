"""Shared tokenizer (plan task T1.10): ``words`` splits text into words by ADR 0001.

The word rule is decided in docs/decisions/0001-word-rule.md; this module implements that
rule and nothing else, so every helper that needs "the words of a text" (``word_count``,
part of ``to_snake_case``, later ``reading_time``) gets the same answer. It is private: the
name starts with ``_``, so it has no public functions, no README row and no CHANGELOG line
(see "Rules for every task" in docs/phases/phase-1-core-helpers.md).
"""

import unicodedata

# Characters that join two letters or digits into one word: "e-mail", "don't", "don’t".
_JOINERS = frozenset("-'’")
# Characters that join two decimal digits only: "3.14", "1,000". Between letters they split
# ("e.g" is two words) so that sentence punctuation without a following space still splits.
_NUMBER_JOINERS = frozenset(".,")


def _is_mark(char: str) -> bool:
    """Return True for a Unicode combining mark (category Mn, Mc or Me)."""
    return unicodedata.category(char).startswith("M")


def words(text: str) -> list[str]:
    """Split ``text`` into words following ADR 0001, in order of appearance.

    A word starts at a character for which ``str.isalnum()`` is true (any script, digits
    included; ``_`` is not one). It continues over further such characters, over combining
    marks (so NFD input such as ``"nai\\u0308ve"`` stays one word), and over a single joiner
    that sits between the word and another ``isalnum()`` character: ``-``, ``'`` or
    ``\\u2019`` always, ``.`` or ``,`` only when the last letter-or-digit before it and the
    character after it are both decimal digits. Anything else (whitespace, other
    punctuation, ``_``, symbols, emoji, a doubled joiner) ends the word and belongs to no
    word. Code points are compared as given; no Unicode normalization is applied.

    Examples: ``"Hello, world!"`` -> ``["Hello", "world"]``, ``"well-known"`` ->
    ``["well-known"]``, ``"3.14"`` -> ``["3.14"]``, ``"e.g."`` -> ``["e", "g"]``,
    ``"foo_bar"`` -> ``["foo", "bar"]``, ``""`` -> ``[]``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), as ``word_count``
            does, rather than splitting some other sequence.
    """
    if not isinstance(text, str):
        raise TypeError(f"words() expects str, got {type(text).__name__}")
    found = []
    start = None  # index where the current word began, None between words
    last_base = ""  # last isalnum() character of the current word
    length = len(text)
    for i, char in enumerate(text):
        if char.isalnum():
            if start is None:
                start = i
            last_base = char
            continue
        if start is not None:
            following = text[i + 1] if i + 1 < length else ""
            if _is_mark(char):
                continue
            if following.isalnum() and (
                char in _JOINERS
                or (char in _NUMBER_JOINERS and last_base.isdecimal() and following.isdecimal())
            ):
                continue
            found.append(text[start:i])
            start = None
    if start is not None:
        found.append(text[start:])
    return found
