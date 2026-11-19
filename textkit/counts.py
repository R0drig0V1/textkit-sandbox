"""Counting helpers. Every public function is listed in the README's function table.

The word rule used here is the one in docs/decisions/0002-what-counts-as-a-word.md; the
shared tokenizer `textkit._tokens.words` implements it and is the single place that rule
lives in code.
`char_freq` counts characters, not words, so that rule does not apply to it.
"""

from textkit import _tokens


def word_count(text: str) -> int:
    """Return the number of words in `text`.

    A word is a maximal run of alphanumeric characters (Unicode-aware, `str.isalnum`), plus
    any combining marks that follow them. A hyphen (`-`, U+2010) or apostrophe (`'`, U+2019)
    between a word character and an alphanumeric character joins both sides into one word
    ("well-known", "don't"); `.` or `,` between two decimal digits does the same ("3.14",
    "1,000,000"). Everything else separates words: whitespace, other punctuation, `_`,
    symbols and emoji. There is no dictionary or language-specific segmentation, so a run
    of CJK characters with no separator is one word. The full rule and its table of cases
    are in ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md).

    Returns 0 for an empty string or text with no alphanumeric character.

    Raises:
        TypeError: if `text` is not a `str`.
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(_tokens.words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in `text`.

    Counting is case-sensitive (`"a"` and `"A"` are different keys) and per code point: no
    Unicode normalization is applied, so a combining mark in NFD text is a key of its own.
    Characters for which `str.isspace()` is true (spaces, tabs, newlines, no-break and other
    Unicode spaces) are not counted. Keys appear in the order of their first occurrence in
    `text`. The result is a new plain `dict`; it is empty for `""` or whitespace-only text.

    Raises:
        TypeError: if `text` is not a `str`.
    """
    if not isinstance(text, str):
        # Without this, a list or bytes would be iterated and counted silently.
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: dict[str, int] = {}
    # A plain dict keeps insertion order (Python 3.7+), which is the first-occurrence order.
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the whole minutes needed to read `text` at `wpm` words per minute.

    Words are counted with `word_count` (the word rule of ADR 0002). The result is the
    number of words divided by `wpm`, rounded **up** to a whole minute (ADR 0004): text with
    no words (`""`, whitespace or punctuation only) takes 0 minutes, and any text with at
    least one word takes at least 1 minute, however high `wpm` is. The division is done in
    integers, so the result is exact for any word count.

    Raises:
        TypeError: if `text` is not a `str`, or `wpm` is not an `int` (`bool` included).
        ValueError: if `wpm < 1`.
    """
    if not isinstance(text, str):
        raise TypeError(f"reading_time() expects str, got {type(text).__name__}")
    # bool is a subclass of int; reading_time(text, True) is a mistake, not "1 wpm". A float
    # would make the integer ceiling below return a float.
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"wpm must be at least 1, got {wpm}")
    # Ceiling division without floats: -(-a // b) == ceil(a / b) for b > 0.
    return -(-word_count(text) // wpm)


# Sentence boundaries follow ADR 0005 (docs/decisions/0005-sentence-boundaries.md).
_TERMINATORS = frozenset(".!?…")
# Characters that may sit between a terminator and the following whitespace ('"Stop." He'),
# and that may open a token before an abbreviation's dot ("(Dr. Lee)").
_CLOSERS = frozenset("\"')]}”’»")
_OPENERS = frozenset("\"'([{“‘«")
# Closed list, compared after casefold(). Abbreviations that often end a sentence (etc., Jr.,
# St.) are left out on purpose: merging two real sentences is the worse error for them.
_ABBREVIATIONS = frozenset({"dr", "mr", "mrs", "ms", "prof", "vs"})


def _is_abbreviation(token: str) -> bool:
    """Whether `token`, written just before a single `.`, makes that dot an abbreviation's."""
    token = token.lstrip("".join(_OPENERS))
    if token.casefold() in _ABBREVIATIONS:
        return True
    # Initials and Latin abbreviations: single letters joined by dots ("J", "e.g", "U.S.A").
    parts = token.split(".")
    return all(len(part) == 1 and part.isalpha() for part in parts)


def _ends_sentence(text: str, run_start: int, run_end: int, next_char: str) -> bool:
    """Whether the terminator run `text[run_start:run_end]` is a boundary (ADR 0005, 2-4).

    `next_char` is the first alphanumeric character after the run, or `""` if there is none.
    The caller has already checked that whitespace or the end of the text follows the run
    and its closers.
    """
    # Rule 3: the next word starts in lowercase, so the sentence goes on. Everything before
    # that word (quotes, brackets, "*", "-", other punctuation) is skipped.
    if next_char.islower():
        return False
    # Rule 4: only a single dot can belong to an abbreviation; "..." and "?" never do.
    if text[run_start:run_end] == ".":
        token_start = run_start
        while token_start > 0 and not text[token_start - 1].isspace():
            token_start -= 1
        if _is_abbreviation(text[token_start:run_start]):
            return False
    return True


def sentence_count(text: str) -> int:
    """Return the number of sentences in `text`.

    A sentence ends at a run of terminators (`.`, `!`, `?`, `…`) followed, after any closing
    quotes or brackets, by whitespace or the end of the text, so `"?!"` and `"..."` end a
    sentence once and `"3.14"` does not end one. The run does not end a sentence when the
    first alphanumeric character after it is a lowercase letter, whatever punctuation comes
    before that (`"Wait... what?"` and `"Hi. *really* bad."` are one sentence each), nor
    when it is a single `.` after an abbreviation: `Dr`, `Mr`, `Mrs`, `Ms`, `Prof`, `vs`
    (any case), or initials such as `J.`, `e.g.`, `U.S.` A piece of text counts as a sentence
    only if it has at least one word by ADR 0002 (`word_count`), so text after the last
    terminator counts and terminators alone do not. Line breaks do not end sentences.
    The full rule, its known miscounts and its table of cases are in ADR 0005
    (docs/decisions/0005-sentence-boundaries.md).

    Returns 0 for an empty string or text with no word.

    Raises:
        TypeError: if `text` is not a `str`.
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects str, got {type(text).__name__}")
    count = 0
    start = 0  # where the current sentence began
    # Index of the first alphanumeric character at or after the latest run (rule 3). It only
    # moves forward, so finding it costs one pass over the text in total, not one per run.
    next_alnum = 0
    i = 0
    while i < len(text):
        if text[i] not in _TERMINATORS:
            i += 1
            continue
        run_start = i
        while i < len(text) and text[i] in _TERMINATORS:
            i += 1
        run_end = i
        while i < len(text) and text[i] in _CLOSERS:
            i += 1
        # Rule 2: a boundary needs whitespace or the end of the text after it.
        if not (i == len(text) or text[i].isspace()):
            continue
        next_alnum = max(next_alnum, i)
        while next_alnum < len(text) and not text[next_alnum].isalnum():
            next_alnum += 1
        next_char = text[next_alnum] if next_alnum < len(text) else ""
        if _ends_sentence(text, run_start, run_end, next_char):
            # Rule 6: the sentence must contain a word; word_count keeps ADR 0002 in one place.
            if word_count(text[start:i]):
                count += 1
            start = i
    if word_count(text[start:]):
        count += 1
    return count
