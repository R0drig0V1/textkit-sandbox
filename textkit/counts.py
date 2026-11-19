"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0002-what-counts-as-a-word.md; the rule
implemented here must stay in step with that ADR and its table of cases. How
``reading_time`` rounds to whole minutes is decided in
docs/decisions/0004-reading-time-rounding.md, with its own table of cases.
"""

import unicodedata

# Characters that join two word characters into one word ("well-known", "don't", "rock’s").
# The typographic apostrophe is included because text pasted from editors uses it.
_WORD_JOINERS = frozenset("-'’")
# Characters that join two decimal digits into one number ("3.14", "1,000").
_NUMBER_JOINERS = frozenset(".,")


def _is_mark(ch: str) -> bool:
    """Return True for combining marks, which belong to the word they follow."""
    return unicodedata.category(ch).startswith("M")


def _joins(text: str, i: int) -> bool:
    """Return True if ``text[i]`` joins the word before it to the character after it.

    The caller guarantees that ``text[i]`` follows a word character.
    """
    if i + 1 >= len(text):
        return False
    ch, after = text[i], text[i + 1]
    if ch in _WORD_JOINERS:
        return after.isalnum()
    if ch in _NUMBER_JOINERS:
        return text[i - 1].isdecimal() and after.isdecimal()
    return False


def word_count(text: str) -> int:
    """Return the number of words in ``text``.

    A word is a maximal run of alphanumeric characters (``str.isalnum``, so any script and
    any digits), plus the combining marks that follow them. A single ``-``, ``'`` or ``’``
    between two alphanumerics joins them into one word (``"well-known"``, ``"don't"``), and
    a single ``.`` or ``,`` between two decimal digits joins them into one number
    (``"3.14"``, ``"1,000"``). Everything else, ``_`` included, separates words; leading
    and trailing joiners are not part of a word. See ADR 0002 for the reasons and the table
    of cases.

    Never raises for a ``str``; ``""``, whitespace-only and punctuation-only text give 0.
    """
    count = 0
    in_word = False
    for i, ch in enumerate(text):
        if ch.isalnum():
            if not in_word:
                count += 1
                in_word = True
        elif in_word and (_is_mark(ch) or _joins(text, i)):
            # Still inside the current word: a combining mark, or a joiner whose next
            # character is alphanumeric (and so continues the word on the next step).
            continue
        else:
            in_word = False
    return count


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
