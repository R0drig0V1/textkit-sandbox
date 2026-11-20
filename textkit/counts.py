"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is fixed by ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md);
T1.10 moves it into the shared tokenizer ``textkit/_tokens.py`` unchanged. ``reading_time``
rounds its word count up to whole minutes, by ADR 0004
(docs/decisions/0004-reading-time-rounds-up.md).
"""

import unicodedata

from textkit._tokens import words

# Characters that join two word parts into one word ("well-known", "don't", "don’t").
_JOINERS = frozenset("-'’")
# Characters that join two runs of decimal digits into one number ("3.14", "1,000").
_DIGIT_JOINERS = frozenset(".,")


def _is_mark(ch: str) -> bool:
    """True for combining marks (Unicode category M*), which continue a word but never start one."""
    return unicodedata.category(ch).startswith("M")


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following ADR 0002.

    A word starts with a letter or digit (``str.isalnum()``) and continues through letters,
    digits and combining marks. One ``-``, ``'`` or ``’`` between a word character and a
    letter or digit keeps the word going (``"well-known"``, ``"don't"``), and so does one
    ``.`` or ``,`` between two decimal digits (``"3.14"``, ``"1,000"``). Every other
    character (whitespace, other punctuation, symbols, ``_``, dashes) separates words.
    ``""`` and text with no letters or digits give 0.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    # The rule lives in the shared tokenizer (T1.10); words() also raises the TypeError.
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is per code point and case-sensitive (``"a"`` and ``"A"`` are separate keys).
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break spaces
    and other Unicode whitespace) are not counted. Keys appear in order of first occurrence.
    No Unicode normalization is applied, so a decomposed ``"ú"`` counts as ``"u"`` plus the
    combining mark U+0301. ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    # A plain dict keeps insertion order (Python 3.7+), which gives first-occurrence order;
    # collections.Counter would too, but returning a plain dict keeps the documented type.
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isspace():
            counts[ch] = counts.get(ch, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read ``text`` at ``wpm`` words per minute (ADR 0004).

    The word count comes from ``word_count`` (ADR 0002) and is rounded **up** to whole
    minutes: ``ceil(word_count(text) / wpm)``. So a text with no words (``""``, whitespace,
    punctuation only) gives 0, any text with at least one word gives at least 1 (under one
    minute reads as 1), and exactly ``wpm`` words give 1 while ``wpm + 1`` give 2.

    Raises:
        TypeError: if ``text`` is not a ``str``, or ``wpm`` is not an ``int`` (``bool`` and
            ``float`` are rejected).
        ValueError: if ``wpm`` is less than 1.
    """
    # bool is a subclass of int; reading_time(text, True) is a bug, not a speed of 1.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"wpm must be an int, not {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, not {wpm}")
    words = word_count(text)
    # Integer ceiling division: exact for any size, no float rounding (ADR 0004).
    return -(-words // wpm)


# The sentence rule of ADR 0005 (docs/decisions/0005-what-ends-a-sentence.md).
_TERMINATORS = frozenset(".!?…")
# Closing quotes and brackets that may sit between a terminator run and the following space.
_CLOSERS = frozenset("\"'”’)]}»")
# Casefolded abbreviations whose single trailing "." never ends a sentence. Kept short on
# purpose: ADR 0005 explains why "etc", "Jr" and "Sr" are not here.
_ABBREVIATIONS = frozenset({"dr", "mr", "mrs", "ms", "prof", "st", "vs", "cf", "e.g", "i.e"})


def _is_abbreviation(text: str, dot: int) -> bool:
    """True if the characters before the ``.`` at ``dot`` form an abbreviation of ADR 0005.

    The candidate runs back from ``dot`` through word characters and ``.`` (so ``"e.g"``
    is one candidate).
    """
    start = dot
    while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "."):
        start -= 1
    return text[start:dot].casefold() in _ABBREVIATIONS


def sentence_count(text: str) -> int:
    """Return the number of sentences in ``text``, following ADR 0005.

    A run of ``.``, ``!``, ``?`` or ``…`` ends a sentence when, after any closing quotes or
    brackets, it is followed by the end of the text or by whitespace; when the next letter
    or digit is not lower case (``"e.g. a hammer"`` and ``"Wait... what?"`` stay one
    sentence); and, for a single ``.``, when the word before it is not one of the
    abbreviations ``Dr``, ``Mr``, ``Mrs``, ``Ms``, ``Prof``, ``St``, ``vs``, ``cf``,
    ``e.g``, ``i.e`` (case-insensitive). Only sentences with at least one letter or digit
    (``str.isalnum()``) count, so a last sentence without a terminator counts and
    punctuation alone does not. ``""`` gives 0. The ADR lists the known miscounts
    (initials, ``"U.S."``, an abbreviation at the real end of a sentence).

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    n = len(text)
    count = 0
    has_word = False  # the current sentence contains a letter or digit
    # Index of the first word character at or after the last look-ahead position (n if
    # none). Look-ahead positions only grow, so caching it keeps the scan linear.
    next_word = -1
    i = 0
    while i < n:
        ch = text[i]
        if ch not in _TERMINATORS:
            if ch.isalnum():
                has_word = True
            i += 1
            continue
        end = i
        while end < n and text[end] in _TERMINATORS:
            end += 1
        if has_word:  # a run before any word ends nothing, so skip the checks
            after = end
            while after < n and text[after] in _CLOSERS:
                after += 1
            ends = after == n or text[after].isspace()
            if ends and after < n:
                if next_word < after:
                    next_word = after
                    while next_word < n and not text[next_word].isalnum():
                        next_word += 1
                ends = next_word == n or not text[next_word].islower()
            if ends and end - i == 1 and ch == "." and _is_abbreviation(text, i):
                ends = False
            if ends:
                count += 1
                has_word = False
        i = end
    return count + (1 if has_word else 0)
