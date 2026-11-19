"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md);
`_words` below implements that rule and nothing else, so the ADR's case table is the spec.
"""

import unicodedata

# Joiners that keep a word together when they sit between a word character and a letter or
# digit (ADR 0002): ASCII hyphen-minus, U+2010 HYPHEN, U+2011 NON-BREAKING HYPHEN, ASCII
# apostrophe, U+2019 RIGHT SINGLE QUOTATION MARK (the typographic apostrophe) and the period.
# En and em dashes are deliberately absent: they separate words ("10–20", "yes—no").
_JOINERS = frozenset("-‐‑'’.")


def _is_mark(char: str) -> bool:
    """Return True for a combining mark (Unicode category Mn, Mc or Me)."""
    return unicodedata.category(char).startswith("M")


def _words(text: str) -> list[str]:
    """Split ``text`` into words with the rule of ADR 0002, in order.

    A word starts at a character for which ``str.isalnum()`` is true and extends over
    alphanumerics and combining marks. A joiner from ``_JOINERS``, or a comma between two
    decimal digits, continues the word only when the next character is alphanumeric (and,
    for the comma, a decimal digit); anything else ends it. Leading and trailing joiners
    are therefore never part of a word.
    """
    words = []
    i, n = 0, len(text)
    while i < n:
        if not text[i].isalnum():
            i += 1
            continue
        start = i
        i += 1
        while i < n:
            char = text[i]
            if char.isalnum() or _is_mark(char):
                i += 1
                continue
            nxt = text[i + 1] if i + 1 < n else ""
            joins = nxt.isalnum() and (
                char in _JOINERS
                # A comma only joins digit groups ("1,000"); between letters it is a typo for
                # ", " and separates ("a,b" is two words).
                or (char == "," and text[i - 1].isdecimal() and nxt.isdecimal())
            )
            if not joins:
                break
            i += 2
        words.append(text[start:i])
    return words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, as defined by ADR 0002.

    A word is a run of letters and digits (``str.isalnum()``, so any script), with the
    combining marks that follow them, kept together by a single hyphen, apostrophe or
    period between two such characters ("well-known", "don't", "3.14", "e.g") or by a
    comma between two digits ("1,000"). Whitespace, other punctuation, symbols, ``_`` and
    en/em dashes separate words and are never counted on their own, so text with no
    letters or digits has 0 words. Never raises for any ``str``; ``""`` gives 0.
    """
    return len(_words(text))
