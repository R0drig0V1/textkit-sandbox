"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0001-word-rule.md and implemented once, in
the shared tokenizer ``textkit._tokens.words`` (plan task T1.10); ``word_count`` only counts
what it returns, so later helpers that need words reuse the same rule without re-deciding it.
How ``reading_time`` rounds a word count to whole minutes is decided in
docs/decisions/0004-reading-time-rounding.md.
Where a sentence ends (abbreviations, ellipses) is decided in
docs/decisions/0005-sentence-boundaries.md and implemented by ``sentence_count``.
"""

from textkit._tokens import words

# Kept under its old name because tests/test_counts.py (which T1.10 must not modify) imports
# ``_words`` from here to check ADR 0001's Words column.
_words = words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following the word rule of ADR 0001.

    A word is a run of letters and digits (``str.isalnum()``, so any script counts), with
    combining marks kept inside it and joined across one ``-``, ``'`` or ``\\u2019`` between
    two letters or digits (``"well-known"``, ``"don't"``: one word each), or across one ``.``
    or ``,`` between two decimal digits (``"3.14"``, ``"1,000"``: one word each). Everything
    else separates words: whitespace, other punctuation, ``_``, symbols, emoji. So ``""``,
    whitespace only and punctuation only all give 0. Scripts written without spaces (Chinese,
    Japanese, Thai) count each unbroken run as one word.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), rather than counting
            the elements of some other iterable.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are separate keys) and per code point:
    no Unicode normalization is applied, so a combining mark in NFD input is its own key.
    Characters for which ``str.isspace()`` is true (spaces, tabs, newlines, no-break
    spaces, ...) are skipped. Keys appear in the order of their first occurrence, which a
    plain ``dict`` keeps (Python 3.7+). ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), as ``word_count`` does,
            rather than counting the elements of some other iterable.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the estimated reading time of ``text`` in whole minutes, rounded up.

    The estimate is ``word_count(text)`` (the word rule of ADR 0001) divided by ``wpm``,
    words per minute, rounded up to a whole minute as decided in ADR 0004: a text with no
    words (``""``, whitespace or punctuation only) gives 0, any text with at least one word
    gives at least 1, and exactly ``k * wpm`` words give ``k``.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), or if ``wpm`` is not
            an ``int`` (``float`` and ``bool`` included).
        ValueError: if ``wpm`` is less than 1.
    """
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects str, got {type(text).__name__}")
    # bool is a subclass of int, but wpm=True is a caller's mistake, not a speed of 1.
    if not isinstance(wpm, int) or isinstance(wpm, bool):
        raise TypeError(f"reading_time() wpm must be int, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() wpm must be at least 1, got {wpm}")
    # Ceiling division in integers: exact for any count, unlike math.ceil(words / wpm).
    return -(-word_count(text) // wpm)


# Sentence rule of docs/decisions/0005-sentence-boundaries.md (plan task T2.2).
_TERMINATORS = frozenset(".!?…。！？")
# Full-width terminators end a sentence with no space after them: the scripts that use them
# (Chinese, Japanese) put none between sentences.
_FULL_WIDTH_TERMINATORS = frozenset("。！？")
# Closing quotes and brackets right after a terminator run belong to the sentence it ends.
_CLOSERS = frozenset("\"'”’»›)]}")
# Abbreviations whose dot ends no sentence even before a capital: titles (always followed by a
# name) and Latin abbreviations that introduce more text. Casefolded, dot included. Kept short
# on purpose (ADR 0005): the capitalization rule already handles every abbreviation that is
# followed by a lower-case word.
_ABBREVIATIONS = frozenset({"mr.", "mrs.", "ms.", "dr.", "prof.", "e.g.", "i.e.", "cf.", "vs."})


def _is_abbreviation(text: str, dot: int) -> bool:
    """Return True if the ``.`` at index ``dot`` ends one of ``_ABBREVIATIONS``.

    The candidate is the run of non-whitespace characters that ends at the dot, without its
    leading characters that are not letters or digits (so ``"(i.e."`` is ``"i.e."``).
    """
    start = dot
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while start < dot and not text[start].isalnum():
        start += 1
    return text[start:dot + 1].casefold() in _ABBREVIATIONS


def _ends_sentence(text: str, run_start: int, after: int, following: str) -> bool:
    """Return True if the terminator run starting at ``run_start`` is a sentence boundary
    under rules 1 to 4 of ADR 0005.

    ``after`` is the index right after the run and its closers; it is only called for runs
    followed by something, so ``text[after]`` exists. ``following`` is the first letter or
    digit at or after ``after`` (``""`` if there is none).
    """
    run_end = run_start
    while run_end < after and text[run_end] in _TERMINATORS:
        run_end += 1
    if any(char in _FULL_WIDTH_TERMINATORS for char in text[run_start:run_end]):
        return True  # rule 1
    if not text[after].isspace():
        return False  # rule 2: "3.14", "example.com", "Hello.World."
    if following.islower():
        return False  # rule 3: "e.g. apples", "Wait... what?", "“Help!” he cried."
    if run_end - run_start == 1 and text[run_start] == "." and _is_abbreviation(text, run_start):
        return False  # rule 4: "Dr. Smith", "e.g. Paris"
    return True


def sentence_count(text: str) -> int:
    """Return the number of sentences in ``text``, following the sentence rule of ADR 0005.

    A run of terminators (``.``, ``!``, ``?``, ``…`` and the full-width ``。``, ``！``,
    ``？``) counts as one, and closing quotes or brackets right after it belong to the
    sentence it ends. The run ends a sentence when it is followed by whitespace and the next
    letter or digit is not lower-case, unless it is the single dot of ``Mr.``, ``Mrs.``,
    ``Ms.``, ``Dr.``, ``Prof.``, ``e.g.``, ``i.e.``, ``cf.`` or ``vs.`` (any case). So
    ``"Dr. Smith is here."``, ``"Use e.g. apples."`` and ``"Wait... what?"`` are one sentence
    each, ``"3.14"`` and ``"example.com"`` never split, and ``"I see... Let us go."`` is two.
    Full-width terminators always end a sentence (``"你好。再见。"`` is two). The end of the
    text ends the last sentence, so a missing final terminator does not matter (``"Hello"``
    is 1). A sentence must contain at least one word by ADR 0001: ``""``, whitespace only
    and punctuation only (``"..."``) all give 0. Newlines are plain whitespace.

    Known divergences from a human count (pinned in the ADR's table): a listed title that
    ends a sentence, an unlisted abbreviation before a capital or a digit, headings without a
    terminator, and sentences that start with a lower-case letter.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included), as ``word_count`` does.
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects str, got {type(text).__name__}")
    count = 0
    start = 0  # start of the current piece of text
    length = len(text)
    ahead = 0  # index of the first letter or digit at or after i; only moves forward
    i = 0
    while i < length:
        if text[i] not in _TERMINATORS:
            i += 1
            continue
        run_start = i
        while i < length and text[i] in _TERMINATORS:
            i += 1
        while i < length and text[i] in _CLOSERS:
            i += 1
        if i == length:
            break  # the end of the text is handled after the loop
        # A forward-only pointer keeps the whole scan linear (no rescan per terminator run).
        ahead = max(ahead, i)
        while ahead < length and not text[ahead].isalnum():
            ahead += 1
        following = text[ahead] if ahead < length else ""
        if _ends_sentence(text, run_start, i, following):
            if words(text[start:i]):
                count += 1
            start = i
    if words(text[start:]):
        count += 1
    return count
