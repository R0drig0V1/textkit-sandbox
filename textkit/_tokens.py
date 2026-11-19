"""Private tokenizer shared by the text helpers (plan task T1.10).

`words` implements the word rule of ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md)
and is its single implementation: `textkit.counts.word_count` is `len(words(text))`, and
`textkit.cases.to_snake_case` uses it where ADR 0001 splits an identifier the same way. The
module name starts with `_`, so it holds no public functions: no README row, no CHANGELOG
line. Changing the rule needs a new ADR and an update of its table and of
`tests/test_tokens.py`.
"""

import unicodedata

# Characters that join two word characters into one word ("well-known", "don't", "rock’s").
# The typographic apostrophe is included because text pasted from editors uses it.
_WORD_JOINERS = frozenset("-'’")
# Characters that join two decimal digits into one number ("3.14", "1,000").
_NUMBER_JOINERS = frozenset(".,")


def _is_mark(ch: str) -> bool:
    """Return True for combining marks, which belong to the word they follow."""
    return unicodedata.category(ch).startswith("M")


def _joins(text: str, i: int) -> bool:
    """Return True if ``text[i]`` joins the word before it to the character after it.

    The caller guarantees that ``text[i]`` follows a word character.
    """
    if i + 1 >= len(text):
        return False
    ch, after = text[i], text[i + 1]
    if ch in _WORD_JOINERS:
        return after.isalnum()
    if ch in _NUMBER_JOINERS:
        return text[i - 1].isdecimal() and after.isdecimal()
    return False


def words(text: str) -> list[str]:
    """Return the words of ``text``, in order, as they appear in it (ADR 0002).

    A word is a maximal run of alphanumeric characters (``str.isalnum``, so any script and
    any digits), plus the combining marks that follow them. A single ``-``, ``'`` or ``’``
    between a word character and an alphanumeric joins them into one word
    (``"well-known"``, ``"don't"``), and a single ``.`` or ``,`` between two decimal digits
    joins them into one number (``"3.14"``, ``"1,000"``). Everything else, ``_`` included,
    separates words; leading and trailing joiners are not part of a word
    (``"'tis"`` -> ``["tis"]``). No normalization or case change is applied: each word is a
    slice of ``text``.

    Never raises for a ``str``; ``""``, whitespace-only and punctuation-only text give ``[]``.
    """
    found: list[str] = []
    start = -1  # Index where the current word starts, or -1 outside a word.
    for i, ch in enumerate(text):
        if ch.isalnum():
            if start < 0:
                start = i
        elif start >= 0 and (_is_mark(ch) or _joins(text, i)):
            # Still inside the current word: a combining mark, or a joiner whose next
            # character is alphanumeric (and so continues the word on the next step).
            continue
        elif start >= 0:
            found.append(text[start:i])
            start = -1
    if start >= 0:
        found.append(text[start:])
    return found
