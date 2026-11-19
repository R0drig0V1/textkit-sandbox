"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is fixed by ADR 0001 (docs/decisions/0001-what-counts-as-a-word.md);
the shared tokenizer `textkit._tokens.words` implements exactly that rule, and `word_count`
counts its result, so every helper built on words splits text the same way.
"""

from textkit import _tokens


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
    return len(_tokens.words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and per code point:
    no Unicode normalization is applied, so a decomposed ``"ú"`` counts as ``"u"`` plus the
    combining acute accent. Characters for which ``str.isspace()`` is true (spaces, tabs,
    newlines, non-breaking spaces, ...) are not counted. Keys appear in order of first
    occurrence, so ``char_freq("abca") == {"a": 2, "b": 1, "c": 1}`` with ``"a"`` first;
    ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects a str, got {type(text).__name__}")
    # A plain dict keeps insertion order (guaranteed since Python 3.7), which is exactly the
    # "order of first occurrence" the plan asks for; collections.Counter would too, but its
    # repr sorts by count, which would hide that order from readers of test failures.
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts
