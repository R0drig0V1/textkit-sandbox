"""Shared tokenizer for textkit (private module: no public functions, no README row).

`words(text)` implements the word rule of the ADR "What counts as a word"
(docs/decisions/0001-what-counts-as-a-word.md) and is the single place that rule lives.
`textkit.counts.word_count` is `len(words(text))`.

`textkit.cases.to_snake_case` does not use it: identifiers split differently (see the
comment above `_SEPARATORS` in `textkit/cases.py`).
"""

import unicodedata

# Characters that join two words into one when they sit between word characters:
# "well-known", "don't", "it’s" (U+2019, the typographic apostrophe).
_JOINERS = frozenset("-'’")
# Characters that join only two digits, so that numbers such as "3.14" and "1,000" stay
# one word while "end.Start" and "a,b" are still two.
_NUMBER_JOINERS = frozenset(".,")


def _is_mark(char: str) -> bool:
    """Return True for a combining mark (Unicode category M*), as in NFD "é"."""
    return unicodedata.category(char).startswith("M")


def words(text: str) -> list[str]:
    """Split `text` into words following the ADR "What counts as a word" (0001).

    A word is a maximal run of alphanumeric characters (`str.isalnum`, so any script),
    plus combining marks that follow one of them, where a single `-`, `'` or `’` between
    two such characters, or a single `.` or `,` between two digits, joins both sides into
    one word. Everything else separates words and is not part of any word. The words are
    returned in order, exactly as they appear in `text` (no case change, no
    normalization); `""` and text with no word characters give `[]`.

    Raises `TypeError` when `text` is not a `str`: iterating bytes or a list would
    silently give wrong words.
    """
    if not isinstance(text, str):
        raise TypeError(f"words() expects a str, got {type(text).__name__}")
    found: list[str] = []
    current: list[str] = []
    last = len(text) - 1
    for i, char in enumerate(text):
        if char.isalnum() or (current and _is_mark(char)):
            current.append(char)
            continue
        if current and i < last and text[i + 1].isalnum():
            if char in _JOINERS:
                current.append(char)
                continue
            # The previous character may be a mark ("é"), which is not a digit,
            # so a number joiner after a mark separates, as it does after a letter.
            if char in _NUMBER_JOINERS and current[-1].isdigit() and text[i + 1].isdigit():
                current.append(char)
                continue
        if current:
            found.append("".join(current))
            current = []
    if current:
        found.append("".join(current))
    return found
