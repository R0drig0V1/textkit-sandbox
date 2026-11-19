"""Shared tokenizer: the single place in code where the word rule of ADR 0002 lives.

`words` implements docs/decisions/0002-what-counts-as-a-word.md exactly; its case table is
tested row by row in tests/test_tokens.py. `word_count` (textkit/counts.py) is `len(words(...))`
and `to_snake_case` (textkit/cases.py) uses it where ADR 0001 and ADR 0002 split the same way.

The module name starts with `_`, so it holds no public functions: no README row, no CHANGELOG
line, and scripts/check.sh skips it. Changing the rule needs a new ADR that supersedes 0002.
"""

import unicodedata

# Characters that join two parts into one word when they sit between a word character and
# an alphanumeric one ("well-known", "don't", "don’t"). U+2010 is the Unicode hyphen; U+2019
# is the typographic apostrophe that word processors substitute for "'".
_HYPHENS = frozenset("-‐")
_APOSTROPHES = frozenset("'’")
# Characters that join two parts only between two decimal digits ("3.14", "1,000"), so that
# a number is one word but "end.Next" or "a,b" are still two.
_DIGIT_SEPARATORS = frozenset(".,")


def _joins(prev: str, char: str, nxt: str) -> bool:
    """Whether `char`, inside a word after `prev` and before `nxt`, keeps the word going."""
    if char in _HYPHENS or char in _APOSTROPHES:
        return nxt.isalnum()
    if char in _DIGIT_SEPARATORS:
        return prev.isdecimal() and nxt.isdecimal()
    return False


def words(text: str) -> list[str]:
    """Split `text` into words by the rule of ADR 0002, in order of appearance.

    A word starts at an alphanumeric character (`str.isalnum`) and continues over
    alphanumeric characters, combining marks (so NFD input splits like NFC input), a hyphen
    (`-`, U+2010) or apostrophe (`'`, U+2019) followed by an alphanumeric character, and a
    `.` or `,` between two decimal digits. Any other character ends the current word and is
    not part of any word: whitespace, other punctuation (`_` included), symbols and emoji.
    Each word is returned exactly as it appears in `text` (no case folding, no
    normalization). Returns `[]` when `text` has no alphanumeric character.

    The argument is not type-checked here; public callers check it so that their error
    message names them. A non-`str` argument fails or misbehaves in unspecified ways.
    """
    found: list[str] = []
    current: list[str] = []
    last = len(text) - 1
    for i, char in enumerate(text):
        if char.isalnum():
            current.append(char)
        elif current and unicodedata.category(char).startswith("M"):
            # A combining mark extends a word but never starts one.
            current.append(char)
        elif current and i < last and _joins(text[i - 1], char, text[i + 1]):
            current.append(char)
        elif current:
            found.append("".join(current))
            current = []
    if current:
        found.append("".join(current))
    return found
