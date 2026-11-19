"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0002-what-counts-as-a-word.md; the rule
is implemented once, in `textkit._tokens.words`, which `word_count` uses. How
``reading_time`` rounds to whole minutes is decided in
docs/decisions/0004-reading-time-rounding.md, with its own table of cases.
"""

from textkit._tokens import words


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a maximal run of alphanumeric characters (``str.isalnum``, so any script and
    any digits), plus the combining marks that follow them. A single ``-``, ``'`` or ``’``
    between two alphanumerics joins them into one word (``"well-known"``, ``"don't"``), and
    a single ``.`` or ``,`` between two decimal digits joins them into one number
    (``"3.14"``, ``"1,000"``). Everything else, ``_`` included, separates words; leading
    and trailing joiners are not part of a word. See ADR 0002 for the reasons and the table
    of cases; the rule is implemented by ``textkit._tokens.words``.

    Never raises for a ``str``; ``""``, whitespace-only and punctuation-only text give 0.
    """
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are separate keys) and works on code
    points: no Unicode normalization is applied, so a precomposed ``"é"`` and ``"e"`` plus a
    combining acute accent are counted as different characters. Characters for which
    ``str.isspace()`` is true (spaces, tabs, newlines, no-break spaces, ...) are skipped. Keys
    appear in the order of their first occurrence, which ``dict`` preserves.

    Never raises for a ``str``; ``""`` and whitespace-only text give ``{}``.
    """
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isspace():
            counts[ch] = counts.get(ch, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read ``text`` at ``wpm`` words per minute.

    Words are counted with ``word_count`` (rule: ADR 0002). The result is the word count
    divided by ``wpm``, rounded up (ADR 0004): a text with no words takes 0 minutes, and any
    text with at least one word takes at least 1, so a short text never reads as "0 min".
    The division is done in integers, so the result is exact for any length.

    Raises ``ValueError`` if ``wpm < 1``, checked before the text is looked at (so
    ``reading_time("", 0)`` raises too).
    """
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, got {wpm!r}")
    # Ceiling division without floats: -(-a // b) == ceil(a / b) for integers, b > 0.
    return -(-word_count(text) // wpm)
