"""Shared word tokenizer (private: no README row, no CHANGELOG line).

`words` implements exactly the word rule of ADR 0001
(docs/decisions/0001-what-counts-as-a-word.md). Every helper that needs "the words of a
text" uses it, so the rule lives in one place: `textkit.counts.word_count` counts its
result, and `textkit.cases.to_snake_case` uses it for the separator step where ADR 0002
splits the same way. Changing the rule needs a new ADR (see ADR 0001, Consequences), and
`tests/test_tokens.py` checks it against ADR 0001's table of cases.

The module name starts with `_`, so `scripts/check.sh` does not treat `words` as public.
"""

import unicodedata

# Characters that join two word characters into one word (ADR 0001, rule 3). The ASCII
# apostrophe and the typographic one (U+2019) are both common in typed prose; the hyphen is
# only the ASCII hyphen-minus, so dashes such as U+2014 separate words.
_APOSTROPHES = "'’"
_HYPHEN = "-"
# Characters that join two decimal digits into one number (ADR 0001, rule 4).
_NUMBER_SEPARATORS = ".,"


def _is_mark(char: str) -> bool:
    """Return True for a combining mark (Unicode category M*), ADR 0001 rule 2."""
    return unicodedata.category(char).startswith("M")


def _joins(text: str, i: int) -> bool:
    """Return True if ``text[i]`` joins the word before it with the character after it.

    Only called while a word is open, so ``text[i - 1]`` is part of that word (ADR 0001,
    rules 3 and 4).
    """
    if i + 1 >= len(text):
        return False
    char, before, after = text[i], text[i - 1], text[i + 1]
    if char in _APOSTROPHES or char == _HYPHEN:
        return after.isalnum()
    if char in _NUMBER_SEPARATORS:
        return before.isdecimal() and after.isdecimal()
    return False


def words(text: str) -> list[str]:
    """Split ``text`` into its words, following ADR 0001, in order of appearance.

    A word starts at a ``str.isalnum`` character (letters and digits of any script) and
    continues over further alphanumerics, over combining marks (so NFC and NFD input split
    the same way), over an apostrophe (``'`` or ``’``) or hyphen (``-``) that has an
    alphanumeric right after it, and over a ``.`` or ``,`` between two decimal digits.
    Every other character ends the word and is not part of any word: whitespace, other
    punctuation, symbols and ``_``. Each word is a slice of ``text``, unchanged (no case
    folding, no normalization): ``words("Don't stop, 3.14!") == ["Don't", "stop", "3.14"]``.
    ``""``, whitespace only and punctuation only give ``[]``.

    Implementation: a single left-to-right scan, linear in ``len(text)``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"words() expects a str, got {type(text).__name__}")
    found = []
    start = None  # index where the open word started, or None outside a word
    for i, char in enumerate(text):
        if char.isalnum():
            if start is None:
                start = i
        elif start is not None and (_is_mark(char) or _joins(text, i)):
            continue
        elif start is not None:
            found.append(text[start:i])
            start = None
    if start is not None:
        found.append(text[start:])
    return found
