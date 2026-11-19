"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md);
the rule is implemented once, by `textkit._tokens.words`, and `word_count` uses it, so the
ADR's case table is the spec. `char_freq` counts characters, not words, and does not use that
rule.
Where `sentence_count` ends a sentence (abbreviations, initials, ellipses) is decided in
ADR 0005 (docs/decisions/0005-sentence-boundaries.md); its case table is that function's spec.
"""

from textkit._tokens import words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, as defined by ADR 0002.

    A word is a run of letters and digits (``str.isalnum()``, so any script), with the
    combining marks that follow them, kept together by a single hyphen, apostrophe or
    period between two such characters ("well-known", "don't", "3.14", "e.g") or by a
    comma between two digits ("1,000"). Whitespace, other punctuation, symbols, ``_`` and
    en/em dashes separate words and are never counted on their own, so text with no
    letters or digits has 0 words. Never raises for any ``str``; ``""`` gives 0.
    """
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Keys are single characters (code points), case-sensitive (``"a"`` and ``"A"`` are
    counted apart), in order of first occurrence in ``text``; values are their counts.
    Every character for which ``str.isspace()`` is true (spaces, tabs, newlines, and
    Unicode spaces such as U+00A0 and U+3000) is skipped. No normalization is applied, so
    an NFD ``"é"`` counts as ``"e"`` plus U+0301 COMBINING ACUTE ACCENT, unlike its NFC
    form. Never raises for any ``str``; ``""`` and whitespace-only text give ``{}``.
    """
    counts: dict[str, int] = {}
    # A plain dict keeps insertion order (guaranteed since Python 3.7), which is exactly
    # "order of first occurrence"; no sorting or Counter needed.
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return how many whole minutes ``text`` takes to read at ``wpm`` words per minute.

    Words are counted with ``word_count`` (ADR 0002). The time is rounded **up** to whole
    minutes (ADR 0004): a text with no words (``""``, whitespace or punctuation only) takes
    0 minutes, any text with 1 to ``wpm`` words takes 1, and exactly ``k * wpm`` words take
    ``k``. The arithmetic is integer-only, so boundaries are exact.

    Raises:
        ValueError: if ``wpm < 1``. ``wpm`` is checked before ``text``, so this is raised
            even for ``""``.
        TypeError: if ``wpm`` (being at least 1) is not an ``int``, or is a ``bool``
            (``200.0``, ``True``).
    """
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, got {wpm!r}")
    # bool is a subclass of int; ``True`` as "1 wpm" is never meant (ADR 0004).
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"wpm must be an int, not {type(wpm).__name__}")
    # Ceiling division without floats: (words + wpm - 1) // wpm == ceil(words / wpm).
    return (word_count(text) + wpm - 1) // wpm


# Sentence rule of ADR 0005 (docs/decisions/0005-sentence-boundaries.md).
# Terminators: period, exclamation mark, question mark and U+2026 HORIZONTAL ELLIPSIS. A run
# of them ("...", "?!", "!!!") is one terminator.
_TERMINATORS = frozenset(".!?…")
# Closing quotes and brackets that may sit between a terminator and the following whitespace
# ('He said "Stop." Then...'): straight and typographic quotes, guillemet, brackets.
_CLOSERS = frozenset("\"'”’»)]}")
# Words that are written with a period and almost never end a sentence, compared after
# str.casefold(). Kept short and English on purpose (ADR 0005): "etc." and "Jr." are left out
# because they often do end a sentence.
_ABBREVIATIONS = frozenset({"mr", "mrs", "ms", "mx", "dr", "prof", "vs", "cf", "e.g", "i.e"})


def _token_before(text: str, end: int) -> str:
    """Return the characters before ``end`` back to the previous whitespace, with leading
    non-alphanumerics dropped ("(Dr" -> "Dr"). Used to spot abbreviations and initials."""
    start = end
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while start < end and not text[start].isalnum():
        start += 1
    return text[start:end]


def _is_boundary(text: str, run_start: int, run_end: int, after: int) -> bool:
    """Decide whether the terminator run ``text[run_start:run_end]`` ends a sentence.

    ``after`` is the index past the run and any closing quotes or brackets; the caller has
    already checked that it is the end of the text or a whitespace character (ADR 0005).
    """
    # A lower-case letter after the gap means the sentence goes on: "e.g. this", "etc. and",
    # "Wait... what?", '"Stop!" he said.' Caseless scripts never trigger this.
    nxt = after
    while nxt < len(text) and text[nxt].isspace():
        nxt += 1
    if nxt < len(text) and text[nxt].islower():
        return False
    # The abbreviation and initial rules only apply to a single period: "Dr..." and "Dr.!"
    # are ellipses or emphasis, not abbreviations.
    if text[run_start:run_end] == ".":
        token = _token_before(text, run_start)
        if token.casefold() in _ABBREVIATIONS:
            return False
        # A single capital letter is an initial ("J. R. R. Tolkien").
        if len(token) == 1 and token.isupper():
            return False
    return True


def sentence_count(text: str) -> int:
    """Return the number of sentences in ``text``, as defined by ADR 0005.

    A sentence ends at a run of terminators (``.``, ``!``, ``?``, ``…``; ``"..."`` and
    ``"?!"`` are one run), optionally followed by closing quotes or brackets, when the run
    is followed by whitespace or the end of the text, except when:

    - the next non-whitespace character is a lower-case letter (``"e.g. this"``,
      ``"Wait... what?"``), or
    - the run is a single period after a listed abbreviation (``Mr``, ``Mrs``, ``Ms``,
      ``Mx``, ``Dr``, ``Prof``, ``vs``, ``cf``, ``e.g``, ``i.e``; any case) or after a single
      capital letter (an initial, ``"J. Smith"``).

    A terminator followed directly by another character (``"3.14"``, ``"wait...what"``,
    ``"end.Next"``) never ends a sentence, and newlines are not terminators. Only pieces that
    contain at least one letter or digit (``str.isalnum()``, so at least one word of ADR
    0002) are counted, so a trailing piece with no terminator counts, and text with no
    letters or digits (``""``, whitespace, ``"!!! ..."``) gives 0. Never raises for any
    ``str``.
    """
    count = 0
    has_word = False
    i, n = 0, len(text)
    while i < n:
        if text[i] not in _TERMINATORS:
            has_word = has_word or text[i].isalnum()
            i += 1
            continue
        run_start = i
        while i < n and text[i] in _TERMINATORS:
            i += 1
        after = i
        while after < n and text[after] in _CLOSERS:
            after += 1
        # "3.14", "wait...what", "end.Next": a terminator glued to the next character is
        # part of the text, not a boundary.
        if after < n and not text[after].isspace():
            continue
        if not _is_boundary(text, run_start, i, after):
            continue
        if has_word:
            count += 1
        has_word = False
        i = after
    # The last piece needs no terminator: "Hello world" is one sentence.
    if has_word:
        count += 1
    return count
