"""Counting helpers. Every public function is listed in the README's function table.

The word rule is the word-rule ADR, docs/decisions/0002-what-counts-as-a-word.md, implemented
once in the shared tokenizer ``textkit._tokens.words``;
the rounding of ``reading_time`` is docs/decisions/0004-reading-time-rounding.md.
"""

from textkit._tokens import words


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a run of letters and digits (``str.isalnum``, so any script), with combining
    marks kept in the word they follow; a hyphen or an apostrophe (``'`` or ``’``) between
    two such characters joins them (``"well-known"``, ``"don't"`` are one word), and so does
    ``.`` or ``,`` between two digits (``"3.14"``, ``"1,000"``). Everything else, the
    underscore and dashes included, separates words. Empty, whitespace-only and
    punctuation-only text gives 0. The full rule and its case table are in
    docs/decisions/0002-what-counts-as-a-word.md.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    # Checked here too so the error names the public function the caller used.
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects a str, got {type(text).__name__}")
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and per code point,
    with no Unicode normalization, so a combining mark counts as a character of its own.
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break spaces
    and the other Unicode whitespace) are not counted. Keys appear in order of first
    occurrence. Empty or whitespace-only text gives ``{}``.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects a str, got {type(text).__name__}")
    # A plain dict keeps insertion order (guaranteed since Python 3.7), which is exactly
    # first-occurrence order; collections.Counter would too, but the contract is a dict.
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read ``text`` at ``wpm`` words per minute.

    Words are counted with ``word_count``. The result is the word count divided by ``wpm``,
    rounded up: text with no words (empty, whitespace or punctuation only) gives 0, any text
    with at least one word gives at least 1, and exactly ``wpm`` words give 1. The rule and
    its case table are in docs/decisions/0004-reading-time-rounding.md.

    Raises ``TypeError`` if ``text`` is not a ``str`` or ``wpm`` is not an ``int`` (``bool``
    is rejected too), and ``ValueError`` if ``wpm < 1``.
    """
    # bool is a subclass of int, but reading_time(text, True) is a mistake, not 1 wpm.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() needs wpm >= 1, got {wpm}")
    # Ceiling division in integers: exact for any size, unlike math.ceil on a float.
    return -(-word_count(text) // wpm)
