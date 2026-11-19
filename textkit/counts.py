"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0002-what-counts-as-a-word.md; that ADR's
case table is the specification, and tests/test_counts.py checks every row of it.
"""

import re

# A word is a run of letters and digits ([^\W_] is \w without the underscore, Unicode-aware
# for str patterns). Runs are joined into one word by a single joiner with a letter or digit
# on both sides: a hyphen or an apostrophe (ASCII ' or typographic U+2019) anywhere, and a
# "." or "," only between two digits, so "3.14" and "1,000" stay whole but "end.Start" does
# not. Anything else, the underscore included, separates words.
_WORD = re.compile(r"[^\W_]+(?:(?:[-'’]|(?<=\d)[.,](?=\d))[^\W_]+)*")


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following ADR 0001.

    A word is a maximal run of letters and digits (any script), where a single hyphen or
    apostrophe between two such characters, or a "." or "," between two digits, keeps the run
    together: ``"well-known"``, ``"don't"`` and ``"3.14"`` are one word each. Everything else
    separates words, so punctuation-only or whitespace-only text has no words and
    ``word_count("") == 0``. No Unicode normalization is applied: combining marks are not
    letters, so in decomposed (NFD) text a mark inside a word splits it; normalize to NFC
    first when that matters.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        # re would accept some non-str objects with a confusing message; be explicit.
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return sum(1 for _ in _WORD.finditer(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and works on code
    points: no Unicode normalization is applied, so a decomposed (NFD) ``"é"`` counts as
    ``"e"`` plus a combining accent. Characters for which ``str.isspace()`` is true (spaces,
    tabs, newlines, non-breaking spaces and other Unicode whitespace) are not counted. Keys
    appear in order of first occurrence; ``char_freq("")`` and whitespace-only text give
    ``{}``.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        # Iterating bytes or a list would "work" and return nonsense keys; be explicit.
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    # A plain dict rather than collections.Counter: the return type is promised as dict, and
    # dicts keep insertion order, which gives "order of first occurrence" for free.
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts
