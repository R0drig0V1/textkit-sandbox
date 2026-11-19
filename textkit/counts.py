"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is fixed by ADR 0001 (docs/decisions/0001-what-counts-as-a-word.md);
the private scanner `_words` below implements exactly that rule, so other counting
functions (and the shared tokenizer planned in T1.10) can reuse it.
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
    """Return True for a combining mark (Unicode category M*)."""
    return unicodedata.category(char).startswith("M")


def _joins(text: str, i: int) -> bool:
    """Return True if ``text[i]`` joins the word before it with the character after it.

    Only called while a word is open, so ``text[i - 1]`` is part of that word.
    """
    if i + 1 >= len(text):
        return False
    char, before, after = text[i], text[i - 1], text[i + 1]
    if char in _APOSTROPHES or char == _HYPHEN:
        return after.isalnum()
    if char in _NUMBER_SEPARATORS:
        return before.isdecimal() and after.isdecimal()
    return False


def _words(text: str) -> list[str]:
    """Split ``text`` into words following ADR 0001.

    A single left-to-right scan: a word starts at an alphanumeric character and grows over
    alphanumerics, combining marks and joiners (see ``_joins``); any other character ends it.
    """
    words = []
    start = None  # index where the open word started, or None outside a word
    for i, char in enumerate(text):
        if char.isalnum():
            if start is None:
                start = i
        elif start is not None and (_is_mark(char) or _joins(text, i)):
            continue
        elif start is not None:
            words.append(text[start:i])
            start = None
    if start is not None:
        words.append(text[start:])
    return words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following ADR 0001.

    A word is a maximal run of letters and digits (``str.isalnum``, so any script), which
    may continue over combining marks, over an apostrophe (``'`` or ``’``) or a hyphen
    (``-``) that has a letter or digit right after it, and over a ``.`` or ``,`` between two
    decimal digits. Everything else separates words: whitespace, other punctuation, symbols
    and ``_``. So ``"well-known"``, ``"don't"`` and ``"3.14"`` are one word each, and
    ``""``, whitespace only or punctuation only give 0.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects a str, got {type(text).__name__}")
    return len(_words(text))
