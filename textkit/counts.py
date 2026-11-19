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
