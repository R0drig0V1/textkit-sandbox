"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is decided in the ADR "What counts as a word"
(docs/decisions/0001-what-counts-as-a-word.md) and implemented once, in the shared
tokenizer `textkit._tokens.words`.
"""

from textkit._tokens import words


def word_count(text: str) -> int:
    """Return the number of words in `text`.

    What counts as a word is decided in the ADR "What counts as a word" (docs/decisions/),
    which ends with the table of cases that tests/test_counts.py checks row by row. In
    short: runs of letters and digits in any script; a single hyphen or apostrophe inside
    a word keeps it whole ("well-known", "don't"); a single "." or "," between digits keeps
    a number whole ("3.14", "1,000"); punctuation and whitespace alone are not words.

    `""`, whitespace-only and punctuation-only text give 0. Raises `TypeError` when `text`
    is not a `str` (iterating bytes or a list would silently give a wrong count).
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects a str, got {type(text).__name__}")
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in `text`.

    Counting is case-sensitive (`"a"` and `"A"` are separate keys) and per code point, with
    no Unicode normalization, so NFC "é" is one key while NFD "é" counts "e" and the
    combining accent separately. Characters for which `str.isspace()` is true (spaces, tabs,
    newlines, U+00A0 and the other Unicode spaces) are not counted. Keys appear in order of
    first occurrence, which a plain `dict` guarantees on Python 3.7+.

    `""` and whitespace-only text give `{}`. Raises `TypeError` when `text` is not a `str`
    (iterating bytes would count integers, a list would count its items).
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects a str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the minutes needed to read `text` at `wpm` words per minute, rounded up.

    Words are counted with `word_count`. Rounding is decided in the ADR "Reading time
    rounding" (docs/decisions/): the result is `ceil(word_count(text) / wpm)`, so text
    with no words gives 0 and any text with at least one word gives at least 1 (a
    15-word note is a 1-minute read, never 0).

    Raises `TypeError` when `text` is not a `str` or `wpm` is not an `int` (`bool` is
    rejected too: `reading_time(text, True)` is a bug, not 1 wpm), and `ValueError` when
    `wpm < 1`. `wpm` is checked before `text` is counted.
    """
    # bool is a subclass of int, so it has to be excluded explicitly.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() needs wpm >= 1, got {wpm}")
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects a str, got {type(text).__name__}")
    # Integer ceiling division: exact for any word count, unlike math.ceil on a float.
    return -(-word_count(text) // wpm)


# Sentence rule: the ADR "Sentence boundaries: abbreviations and ellipses" (docs/decisions/).
# "!" and "?" always end a sentence; "." and "…" depend on the rules below.
_STRONG_ENDS = frozenset("!?")
_END_MARKS = _STRONG_ENDS | frozenset(".…")
# Closing quotes and brackets that may follow an end mark before the space: 'said "Stop." Then'.
_CLOSERS = frozenset("\"'”’)]}»")
# Opening quotes and brackets that may precede the next word: '... "maybe".'
_OPENER_CHARS = "\"'“‘([{«"
_OPENERS = frozenset(_OPENER_CHARS)
# Abbreviations that a sentence goes on after: titles before a name and the Latin
# introducers. Compared lower-case, without the final dot.
_NEVER_FINAL = frozenset({"mr", "mrs", "ms", "dr", "prof", "st", "vs", "cf", "e.g", "i.e"})
# Abbreviations that often end a sentence, so they end one only before a non-lower-case
# word, like an ellipsis.
_MAYBE_FINAL = frozenset({"etc"})


def _next_word_is_lower(text: str, pos: int) -> bool:
    """Return True when the first character after `pos`, past spaces and openers, is lower-case."""
    n = len(text)
    while pos < n and (text[pos].isspace() or text[pos] in _OPENERS):
        pos += 1
    return pos < n and text[pos].islower()


def _ends_sentence(text: str, start: int, mark_start: int, mark: str, after: int) -> bool:
    """Decide whether the end mark `mark` at `text[mark_start:]` closes the sentence.

    `start` is where the current sentence began and `after` the index past the mark and any
    closers (already known to be whitespace or the end of the text).
    """
    if any(char in _STRONG_ENDS for char in mark):
        return True
    if mark != ".":
        # "...", "..", "…" and mixes of them: an ellipsis.
        return not _next_word_is_lower(text, after)
    before = text[start:mark_start].split()
    token = before[-1].lstrip(_OPENER_CHARS).lower() if before else ""
    if token in _NEVER_FINAL:
        return False
    if token in _MAYBE_FINAL:
        return not _next_word_is_lower(text, after)
    return True


def sentence_count(text: str) -> int:
    """Return the number of sentences in `text`.

    The rule is decided in the ADR "Sentence boundaries: abbreviations and ellipses"
    (docs/decisions/), which ends with the table of cases that tests/test_counts.py checks
    row by row. In short: a run of `.`, `!`, `?` or `…` ends a sentence when whitespace or
    the end of the text follows it (closing quotes and brackets in between are allowed), so
    `"3.14"` and `"example.com"` do not split. `!` or `?` always ends one. A single `.`
    after `Mr`, `Mrs`, `Ms`, `Dr`, `Prof`, `St`, `vs`, `cf`, `e.g` or `i.e` (any case)
    never does. An ellipsis (`...`, `…`) or `etc.` ends one unless the next word starts
    with a lower-case letter (`"Wait... what?"` is one sentence). Only stretches that
    contain at least one word (an alphanumeric character) count, and text with no end mark
    is one sentence, so `""` and punctuation-only text give 0.

    Raises `TypeError` when `text` is not a `str`.
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects a str, got {type(text).__name__}")
    count = 0
    start = 0
    i = 0
    n = len(text)
    while i < n:
        if text[i] not in _END_MARKS:
            i += 1
            continue
        mark_end = i
        while mark_end < n and text[mark_end] in _END_MARKS:
            mark_end += 1
        after = mark_end
        while after < n and text[after] in _CLOSERS:
            after += 1
        # Only whitespace or the end of the text after the mark makes a boundary; the end
        # of the text closes the last sentence below anyway.
        if after < n and text[after].isspace() and _ends_sentence(
            text, start, i, text[i:mark_end], after
        ):
            # Any alphanumeric character starts a word under the ADR "What counts as a
            # word", so this is "the stretch contains a word" without its tokenizer.
            if any(char.isalnum() for char in text[start:after]):
                count += 1
            start = after
        i = after
    if any(char.isalnum() for char in text[start:]):
        count += 1
    return count
