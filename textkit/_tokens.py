"""Shared word tokenizer (plan task T1.10). Private: not part of the public API.

``words`` implements exactly the word rule of docs/decisions/0002-what-counts-as-a-word.md;
that ADR's case table is the specification and tests/test_tokens.py checks every row of it.
``textkit.counts.word_count`` counts these words, and ``textkit.cases.to_snake_case`` uses
them for the inputs where that rule and docs/decisions/0001-snake-case-capital-runs.md agree.
"""

import re

# A word is a run of letters and digits ([^\W_] is \w without the underscore, Unicode-aware
# for str patterns). Runs are joined into one word by a single joiner with a letter or digit
# on both sides: a hyphen or an apostrophe (ASCII ' or typographic U+2019) anywhere, and a
# "." or "," only between two digits, so "3.14" and "1,000" stay whole but "end.Start" does
# not. Anything else, the underscore included, separates words.
_WORD = re.compile(r"[^\W_]+(?:(?:[-'’]|(?<=\d)[.,](?=\d))[^\W_]+)*")


def words(text: str) -> list[str]:
    """Return the words of ``text`` in order, as defined by 0002-what-counts-as-a-word.

    A word is a maximal run of letters and digits (any script), where a single hyphen or
    apostrophe between two such characters, or a "." or "," between two digits, keeps the run
    together: ``words("don't stop, well-known 3.14")`` is
    ``["don't", "stop", "well-known", "3.14"]``. Everything else, ``_`` included, separates
    words and is dropped, so punctuation-only or whitespace-only text gives ``[]``. No Unicode
    normalization is applied: in decomposed (NFD) text a combining mark inside a word splits
    it.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        # re would accept bytes and fail later with a confusing message; be explicit.
        raise TypeError(f"words() expects str, got {type(text).__name__}")
    return _WORD.findall(text)
