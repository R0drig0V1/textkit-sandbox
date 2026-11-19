"""Shared tokenizer: the character classes and the word rule of ADR 0001 (private module).

docs/decisions/0001-what-counts-as-a-word.md defines a word in two layers, and this module
exposes both because its two users need different layers:

- ``char_class(char)`` maps one character to its ADR 0001 class: ``DIGIT``, ``LETTER``,
  ``MARK``, ``JOINER``, ``NUM_SEP`` or ``OTHER``.
- ``words(text)`` applies the word regular expression of ADR 0001 over those classes and
  returns the words in order. ``textkit.counts.word_count`` is ``len(words(text))``.

``textkit.cases.to_snake_case`` uses only ``char_class``. ADR 0002 splits identifiers on
the same classes (letters and digits make words, a combining mark continues the word it
follows, everything else separates), but not on the word regex: in an identifier ``-`` and
``.`` always separate (``"kebab-case"`` is two words), while ADR 0001 joins
``"well-known"`` and ``"3.14"``. ``to_snake_case`` also splits at case changes, which ADR
0001 never does. So it reads the classes and keeps its own splitting loop; for it ``JOINER``
and ``NUM_SEP`` are separators like ``OTHER``.

This module is private (the leading underscore): it is not part of the public API, has no
README row, and its names may change with the helpers that use it. Any change to what
``words`` returns changes ``word_count`` (and so ``reading_time``) and needs a new ADR;
any change to ``char_class`` also changes ``to_snake_case`` and needs ADR 0002 updated.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

# Class letters of ADR 0001. Each character of the text is mapped to one of them, and the
# word rule is then a plain regular expression over that class string. This keeps the rule
# exact for any Unicode input: the stdlib ``re`` cannot express "letter or combining mark"
# directly, but it can match a string of class letters.
DIGIT = "D"  # str.isdecimal(): 0-9 and the decimal digits of other scripts
LETTER = "L"  # str.isalnum() and not a decimal digit: letters, other numerics (², Ⅻ)
MARK = "M"  # Unicode general category M*: combining accents, Indic vowel signs
JOINER = "J"  # joins two word characters: hyphens and apostrophes
NUM_SEP = "S"  # joins two decimal digits only: "3.14", "1,000"
OTHER = "O"  # everything else separates words: spaces, punctuation, symbols, "_"

_JOINERS = frozenset("-‐‑'’")  # hyphen-minus, hyphen, non-breaking hyphen,
# apostrophe, right single quotation mark (the typographic apostrophe)
_NUM_SEPS = frozenset(".,")

# A word starts with a letter or digit and continues with letters, digits and marks. A
# joiner continues it only when a letter or digit follows; "." or "," continues it only
# when a digit is on both sides. The class letters above are spelled out here so the
# pattern reads exactly as the one printed in ADR 0001.
_WORD = re.compile(r"[LD][LDM]*(?:(?:J[LD]|(?<=D)SD)[LDM]*)*")


def char_class(char: str) -> str:
    """Return the ADR 0001 class of one character: one of the class constants above.

    The checks run in the ADR's order (digit, letter, mark, joiner, number separator,
    other), so every character gets exactly one class. ``char`` must be exactly one
    character: for a longer string the result means nothing, and ``unicodedata.category``
    may raise ``TypeError``.
    """
    if char.isdecimal():
        return DIGIT
    if char.isalnum():
        return LETTER
    if unicodedata.category(char).startswith("M"):
        return MARK
    if char in _JOINERS:
        return JOINER
    if char in _NUM_SEPS:
        return NUM_SEP
    return OTHER


def words(text: str) -> List[str]:
    """Return the words of ``text`` in order, as defined by ADR 0001.

    Each word is a slice of ``text`` (nothing is normalised or lower-cased); characters
    that belong to no word are dropped. Returns ``[]`` for an empty string or one with no
    letters or digits. ``text`` must be a ``str``: this private helper does not check the
    type, the public callers do (``word_count`` raises ``TypeError``).
    """
    classes = "".join(char_class(char) for char in text)
    return [text[m.start() : m.end()] for m in _WORD.finditer(classes)]
