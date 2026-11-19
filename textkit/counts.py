"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0001-what-counts-as-a-word.md; the
private ``_words`` below is the reference implementation of that rule, written so that the
shared tokenizer (plan task T1.10, ``textkit/_tokens.py``) can take it over unchanged.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

# Character classes of ADR 0001. Each character of the text is mapped to one class letter,
# and the word rule is then a plain regular expression over that class string. This keeps
# the rule exact for any Unicode input: the stdlib ``re`` cannot express "letter or
# combining mark" directly, but it can match a string of class letters.
_DIGIT = "D"  # str.isdecimal(): 0-9 and the decimal digits of other scripts
_LETTER = "L"  # str.isalnum() and not a decimal digit: letters, other numerics (2, XII)
_MARK = "M"  # Unicode general category M*: combining accents, Indic vowel signs
_JOINER = "J"  # joins two word characters: hyphens and apostrophes
_NUM_SEP = "S"  # joins two decimal digits only: "3.14", "1,000"
_OTHER = "O"  # everything else separates words: spaces, punctuation, symbols, "_"

_JOINERS = frozenset("-‐‑'’")  # hyphen-minus, hyphen, non-breaking hyphen,
# apostrophe, right single quotation mark (the typographic apostrophe)
_NUM_SEPS = frozenset(".,")

# A word starts with a letter or digit and continues with letters, digits and marks. A
# joiner continues it only when a letter or digit follows; "." or "," continues it only
# when a digit is on both sides.
_WORD = re.compile(r"[LD][LDM]*(?:(?:J[LD]|(?<=D)SD)[LDM]*)*")


def _char_class(char: str) -> str:
    """Return the ADR 0001 class letter of one character."""
    if char.isdecimal():
        return _DIGIT
    if char.isalnum():
        return _LETTER
    if unicodedata.category(char).startswith("M"):
        return _MARK
    if char in _JOINERS:
        return _JOINER
    if char in _NUM_SEPS:
        return _NUM_SEP
    return _OTHER


def _words(text: str) -> List[str]:
    """Return the words of ``text`` in order, as defined by ADR 0001."""
    classes = "".join(_char_class(char) for char in text)
    return [text[m.start() : m.end()] for m in _WORD.finditer(classes)]


def word_count(text: str) -> int:
    """Count the words in ``text`` by the rule of ADR 0001.

    A word is a run of letters, digits and combining marks (any script) that starts with a
    letter or digit. A hyphen or apostrophe between two such characters keeps the word
    together (``"well-known"``, ``"don't"``), as does ``.`` or ``,`` between two digits
    (``"3.14"``, ``"1,000"``). Everything else separates words: whitespace, other
    punctuation (dashes, ``/``, ``_``, ``@``), symbols and emoji. Scripts written without
    spaces (Chinese, Japanese) are not segmented: a run of their characters is one word.

    Returns 0 for an empty string or one with no letters or digits.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` and ``None`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(_words(text))
