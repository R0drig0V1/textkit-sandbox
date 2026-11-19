"""Shared word tokenizer for textkit (private: no README row, no CHANGELOG line).

``words`` implements the word rule of ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md)
exactly and is its reference implementation: the ADR's case table is the spec, and
``tests/test_tokens.py`` asserts every row of it. ``textkit.counts.word_count`` counts with it
and ``textkit.cases.to_snake_case`` uses it where ADR 0001's identifier rules split the same
way. Changing the rule needs a new ADR that supersedes 0002 (see its Consequences).

The module name starts with ``_`` so that ``scripts/check.sh`` does not treat ``words`` as a
public function (plan, "Rules for every task").
"""

import unicodedata

# Class J of ADR 0002: joiners that keep a word together when they sit between a word
# character and an alphanumeric. ASCII hyphen-minus, U+2010 HYPHEN, U+2011 NON-BREAKING
# HYPHEN, ASCII apostrophe, U+2019 RIGHT SINGLE QUOTATION MARK (the typographic apostrophe)
# and the period. En and em dashes are deliberately absent: they separate ("10–20", "yes—no").
_JOINERS = frozenset("-‐‑'’.")


def _is_mark(char: str) -> bool:
    """Return True for a combining mark (class M of ADR 0002: category Mn, Mc or Me)."""
    return unicodedata.category(char).startswith("M")


def words(text: str) -> list[str]:
    """Split ``text`` into its words, in order, with the word rule of ADR 0002.

    A word starts at a character for which ``str.isalnum()`` is true (any script; a combining
    mark never starts one) and extends over alphanumerics and the combining marks that follow
    them. A single joiner (hyphen ``-`` U+2010 U+2011, apostrophe ``'`` U+2019, or period),
    or a comma between two decimal digits, continues the word only when the next character is
    alphanumeric (a decimal digit, for the comma); any other character ends it. So
    ``"well-known"``, ``"don't"``, ``"3.14"`` and ``"1,000"`` are one word each, while
    leading and trailing joiners, whitespace, other punctuation, symbols, ``_`` and en/em
    dashes are never part of a word.

    The words are substrings of ``text``, unchanged: no case folding and no Unicode
    normalization (NFD input gives NFD words). Text with no letters or digits, ``""``
    included, gives ``[]``. Never raises for a ``str``.
    """
    found = []
    i, n = 0, len(text)
    while i < n:
        # Step 1: skip to the next alphanumeric; only class A starts a word.
        if not text[i].isalnum():
            i += 1
            continue
        start = i
        i += 1
        while i < n:
            char = text[i]
            # Step 2: alphanumerics and combining marks extend the word.
            if char.isalnum() or _is_mark(char):
                i += 1
                continue
            # Steps 3 and 4: a joiner, or a comma between decimal digits, links two segments
            # only when an alphanumeric follows; then both characters belong to the word.
            nxt = text[i + 1] if i + 1 < n else ""
            joins = nxt.isalnum() and (
                char in _JOINERS
                # A comma only joins digit groups ("1,000"); between letters it is a typo for
                # ", " and separates ("a,b" is two words).
                or (char == "," and text[i - 1].isdecimal() and nxt.isdecimal())
            )
            if not joins:
                # Step 5: anything else ends the word, before this character.
                break
            i += 2
        found.append(text[start:i])
    return found
