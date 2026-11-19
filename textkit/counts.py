"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is fixed by ADR 0001 (docs/decisions/0001-what-counts-as-a-word.md);
the shared tokenizer `textkit._tokens.words` implements exactly that rule, and `word_count`
counts its result, so every helper built on words splits text the same way.
"""

from textkit import _tokens


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following ADR 0001.

    A word is a maximal run of letters and digits (``str.isalnum``, so any script), which
    may continue over combining marks, over an apostrophe (``'`` or ``’``) or a hyphen
    (``-``) that has a letter or digit right after it, and over a ``.`` or ``,`` between two
    decimal digits. Everything else separates words: whitespace, other punctuation, symbols
    and ``_``. So ``"well-known"``, ``"don't"`` and ``"3.14"`` are one word each, and
    ``""``, whitespace only or punctuation only give 0.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects a str, got {type(text).__name__}")
    return len(_tokens.words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and per code point:
    no Unicode normalization is applied, so a decomposed ``"ú"`` counts as ``"u"`` plus the
    combining acute accent. Characters for which ``str.isspace()`` is true (spaces, tabs,
    newlines, non-breaking spaces, ...) are not counted. Keys appear in order of first
    occurrence, so ``char_freq("abca") == {"a": 2, "b": 1, "c": 1}`` with ``"a"`` first;
    ``""`` and whitespace-only text give ``{}``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects a str, got {type(text).__name__}")
    # A plain dict keeps insertion order (guaranteed since Python 3.7), which is exactly the
    # "order of first occurrence" the plan asks for; collections.Counter would too, but its
    # repr sorts by count, which would hide that order from readers of test failures.
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the minutes needed to read ``text`` at ``wpm`` words per minute (ADR 0004).

    Words are counted with ``word_count`` (ADR 0001). The result is whole minutes rounded
    **up**: any text with at least one word takes at least 1 minute, and only text with no
    words (``""``, whitespace or punctuation only) gives 0. So with the default 200 wpm,
    1 to 200 words give 1, 201 words give 2. The division is done on integers, so there is
    no floating-point rounding at exact multiples of ``wpm``.

    Raises:
        TypeError: if ``text`` is not a ``str``, or ``wpm`` is not an ``int`` (``bool`` is
            rejected too, although it is a subclass of ``int``).
        ValueError: if ``wpm < 1``.
    """
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects a str, got {type(text).__name__}")
    # bool is checked explicitly because isinstance(True, int) is True, and reading_time(t,
    # True) is almost certainly a bug rather than a request for 1 word per minute.
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, got {wpm}")
    # Ceiling division on integers: -(-a // b) == ceil(a / b) for b > 0, exact for any size.
    return -(-word_count(text) // wpm)


# Sentence boundaries follow ADR 0005 (docs/decisions/0005-sentence-boundaries.md).
# Terminators (rule 1): a run of them, ellipses included, is one candidate boundary.
_TERMINATORS = ".!?…"
# Closing quotes and brackets that may follow a terminator run and belong to it (rule 1).
_CLOSERS = "\"'”’)]}»"
# Titles that come before a name, so their period never ends a sentence (rule 4). Kept tiny
# on purpose: abbreviations that often end a sentence ("etc.", "Jr.", "St.") are left out.
_TITLES = frozenset({"Mr", "Mrs", "Ms", "Dr", "Prof"})


def _word_before(text: str, i: int) -> str:
    """Return the run of alphanumeric characters that ends right before ``text[i]``."""
    start = i
    while start > 0 and text[start - 1].isalnum():
        start -= 1
    return text[start:i]


def sentence_count(text: str) -> int:
    """Return the number of sentences in ``text``, following ADR 0005.

    A run of ``.``, ``!``, ``?`` and ``…`` (so ``"?!"`` and ``"..."`` are one), with any
    closing quotes or brackets after it, ends a sentence only when whitespace or the end of
    the text follows it, and the next letter or digit is not lowercase. A single ``.`` after
    ``Mr``, ``Mrs``, ``Ms``, ``Dr`` or ``Prof`` never ends a sentence. Only stretches that
    contain a letter or digit count. So ``"e.g. a hammer"``, ``"Wait... what?"``, ``"3.14"``
    and ``"Dr. Smith"`` do not split a sentence, ``""`` and punctuation only give 0, and text
    with no terminator is one sentence. Known misses (``"Use e.g. Python."`` gives 2) are
    listed in the ADR.

    Raises:
        TypeError: if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects a str, got {type(text).__name__}")
    count = 0
    in_sentence = False  # the current sentence has a letter or digit (rule 5)
    # A boundary that passed rules 2 and 4 but waits for the next letter or digit (rule 3).
    # Deciding there keeps the scan linear: no look-ahead over the rest of the text.
    pending = False
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char.isalnum():
            if pending and not char.islower():
                count += 1  # the previous sentence ended; this character starts a new one
            pending = False
            in_sentence = True
            i += 1
        elif char in _TERMINATORS:
            run_end = i
            while run_end < n and text[run_end] in _TERMINATORS:
                run_end += 1
            after = run_end
            while after < n and text[after] in _CLOSERS:
                after += 1
            followed_by_space = after == n or text[after].isspace()  # rule 2
            is_title = run_end - i == 1 and text[i] == "." and _word_before(text, i) in _TITLES
            if in_sentence and followed_by_space and not is_title:
                pending = True
            i = after
        else:
            i += 1
    if in_sentence:
        count += 1  # the last sentence, ended by a terminator or by the end of the text
    return count
