"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0001-word-rule.md; `_words` implements
that rule and nothing else, so later helpers (and the shared tokenizer of plan task T1.10)
can reuse it without re-deciding it.
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


def _words(text: str) -> list[str]:
    """Split ``text`` into words following ADR 0001 (see the module docstring).

    A word starts at a character for which ``str.isalnum()`` is true. It continues over
    further such characters, over combining marks (so NFD input such as ``"nai\\u0308ve"``
    stays one word), and over a single joiner that sits between the word and another
    ``isalnum()`` character: ``-``, ``'`` or ``\\u2019`` always, ``.`` or ``,`` only when the
    last letter-or-digit before it and the character after it are both decimal digits.
    Anything else ends the word and is otherwise ignored.
    """
    words = []
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
            words.append(text[start:i])
            start = None
    if start is not None:
        words.append(text[start:])
    return words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following the word rule of ADR 0001.

    A word is a run of letters and digits (``str.isalnum()``, so any script counts), with
    combining marks kept inside it and joined across one ``-``, ``'`` or ``\\u2019`` between
    two letters or digits (``"well-known"``, ``"don't"``: one word each), or across one ``.``
    or ``,`` between two decimal digits (``"3.14"``, ``"1,000"``: one word each). Everything
    else separates words: whitespace, other punctuation, ``_``, symbols, emoji. So ``""``,
    whitespace only and punctuation only all give 0. Scripts written without spaces (Chinese,
    Japanese, Thai) count each unbroken run as one word.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), rather than counting
            the elements of some other iterable.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(_words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are separate keys) and per code point:
    no Unicode normalization is applied, so a combining mark in NFD input is its own key.
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break
    spaces, ...) are skipped. Keys appear in the order of their first occurrence, which a
    plain ``dict`` keeps (Python 3.7+). ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), as ``word_count`` does,
            rather than counting the elements of some other iterable.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts
