"""The shared tokenizer: the single word rule of textkit (ADR 0001).

docs/decisions/0001-what-counts-as-a-word.md defines what a word is; this module is its only
implementation, so every helper that needs words (``word_count``, ``to_snake_case`` where the
rules agree, and later tasks) splits text the same way. Change the ADR before changing the
rule here: every count in textkit moves with it.

The module is private (its name starts with ``_``): nothing here is part of the public API,
appears in the README function table or gets a CHANGELOG line, so ``words`` and
``is_word_char`` carry no leading underscore of their own.
"""

import unicodedata

# Characters that join two word runs into one word: the ASCII hyphen-minus, the ASCII
# apostrophe and the typographic apostrophe U+2019 (what most editors type for "don't").
_JOINERS = "-'’"
# Characters that join two runs only between decimal digits ("3.14", "1,000").
_DIGIT_JOINERS = ".,"


def is_word_char(ch: str) -> bool:
    """Return True for letters, numbers and combining marks (Unicode categories L, N, M).

    Combining marks count so that decomposed (NFD) text such as "cafe\\u0301" stays one word.
    ``ch`` must be a single character; ``unicodedata.category`` raises ``TypeError`` otherwise.
    """
    return unicodedata.category(ch)[0] in "LNM"


def _joins(text: str, i: int) -> bool:
    """Return True if ``text[i]`` joins the word run before it to the one after it.

    The caller guarantees that ``text[i - 1]`` is a word character.
    """
    if i + 1 >= len(text) or not is_word_char(text[i + 1]):
        return False
    ch = text[i]
    if ch in _JOINERS:
        return True
    if ch in _DIGIT_JOINERS:
        return text[i - 1].isdecimal() and text[i + 1].isdecimal()
    return False


def words(text: str) -> list[str]:
    """Split ``text`` into its words, in order, following ADR 0001.

    A word is a maximal run of letters, digits and combining marks (any script), where a
    single hyphen or apostrophe (``'`` or ``’``) between two such characters joins them
    (``"well-known"``, ``"don't"``), and a single ``.`` or ``,`` between two decimal digits
    does too (``"3.14"``, ``"1,000"``). Everything else separates words and is dropped:
    whitespace, other punctuation, symbols and ``_`` (``"snake_case"`` -> ``["snake",
    "case"]``). Words are returned exactly as written: no case folding, no normalization.

    ``""``, whitespace only and punctuation only give ``[]``.

    ``text`` must be a ``str``; callers check the type (``word_count`` raises ``TypeError``).
    """
    found = []
    start = None
    for i, ch in enumerate(text):
        if is_word_char(ch):
            if start is None:
                start = i
        elif start is not None and not _joins(text, i):
            found.append(text[start:i])
            start = None
    if start is not None:
        found.append(text[start:])
    return found
