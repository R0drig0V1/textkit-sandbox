"""Counting helpers. Every public function is listed in the README's function table.

The word rule is the word-rule ADR, docs/decisions/0002-what-counts-as-a-word.md, implemented
once in the shared tokenizer ``textkit._tokens.words``;
the rounding of ``reading_time`` is docs/decisions/0004-reading-time-rounding.md;
the sentence rule of ``sentence_count`` is docs/decisions/0005-sentence-boundaries.md.
"""

from typing import Optional

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


# Characters that can end a sentence (sentence ADR, rule 1). "…" is U+2026.
_TERMINATORS = frozenset(".!?…")
# Closing quotes and brackets that stay with the terminator run before them (rule 1).
_CLOSERS = frozenset("\"'”’»)]}")
# Opening quotes and brackets stripped from the front of a word before the abbreviation
# lookup, so "(Dr." and "“e.g." are recognised (rule 3).
_OPENERS = frozenset("\"'“‘«([{")
# Abbreviations whose final "." never ends a sentence (rule 3), compared after casefold().
# Titles that come before a name, and Latin abbreviations that introduce more text. "etc."
# is left out on purpose: it ends sentences too often (see the ADR).
_ABBREVIATIONS = frozenset({"mr", "mrs", "ms", "dr", "prof", "st", "e.g", "i.e", "cf", "vs"})


def _is_ellipsis(run: str) -> bool:
    """True for a terminator run made only of dots, with two or more of them or a "…"."""
    return not (set(run) - {".", "…"}) and (len(run) > 1 or run == "…")


def _word_before(text: str, end: int) -> str:
    """Return the non-whitespace characters right before ``end``, leading openers removed."""
    start = end
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while start < end and text[start] in _OPENERS:
        start += 1
    return text[start:end]


def _next_word_char(text: str, start: int) -> Optional[str]:
    """Return the first ``str.isalnum`` character at or after ``start``, or None."""
    for i in range(start, len(text)):
        if text[i].isalnum():
            return text[i]
    return None


def _ends_sentence(text: str, start: int, end: int) -> bool:
    """Decide whether the terminator run ``text[start:end]`` (closers included) ends a sentence.

    Applies rules 2 to 4 of the sentence ADR; the caller has checked that a word comes before.
    """
    if end < len(text) and not text[end].isspace():
        # Rule 2: "3.14", "v2.0", the inner dot of "e.g." and "Hello.World" do not end one.
        return False
    run = text[start:end].rstrip("".join(_CLOSERS))
    if run == "." and _word_before(text, start).casefold() in _ABBREVIATIONS:
        return False  # Rule 3.
    if _is_ellipsis(run):
        # Rule 4: a trailing-off ellipsis continues the sentence when a lowercase word follows.
        following = _next_word_char(text, end)
        return following is None or not following.islower()
    return True


def sentence_count(text: str) -> int:
    """Return the number of sentences in ``text``.

    A sentence ends at a run of ``.``, ``!``, ``?`` or ``…`` (a run such as ``"?!"`` or
    ``"..."`` ends one sentence, and closing quotes or brackets right after it belong to it)
    when whitespace or the end of the text follows the run. So the dots of ``"3.14"`` and
    the inner dot of ``"e.g."`` never end a sentence. Two exceptions: a single ``.`` after a
    known abbreviation (``Dr.``, ``Mr.``, ``e.g.``, ``i.e.`` and a few more) does not end
    one, and an ellipsis (``"..."`` or ``"…"``) does not end one when the next word starts
    with a lowercase letter. Only stretches that contain at least one word (the word rule of
    ``word_count``) count, so empty, whitespace-only and punctuation-only text gives 0, and
    text with words but no terminal punctuation gives 1. Newlines do not end sentences. The
    full rule and its case table are in docs/decisions/0005-sentence-boundaries.md.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects a str, got {type(text).__name__}")
    count = 0
    # Whether the sentence being read has a word yet. A word starts with an isalnum
    # character under the word rule, so checking for one is enough (rule 5).
    has_word = False
    i, n = 0, len(text)
    while i < n:
        if text[i] not in _TERMINATORS:
            has_word = has_word or text[i].isalnum()
            i += 1
            continue
        start = i
        while i < n and text[i] in _TERMINATORS:
            i += 1
        while i < n and text[i] in _CLOSERS:
            i += 1
        if has_word and _ends_sentence(text, start, i):
            count += 1
            has_word = False
    # Rule 5: words after the last terminator (or with no terminator at all) are a sentence.
    return count + has_word
