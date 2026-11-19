"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0002-what-counts-as-a-word.md; that ADR's
case table is the specification, and tests/test_counts.py checks every row of it. The rule
itself lives in the shared tokenizer, textkit/_tokens.py, so every helper splits words alike.
How `reading_time` rounds to whole minutes is decided in
docs/decisions/0006-reading-time-rounding.md. Where `sentence_count` ends a sentence
(abbreviations, ellipses) is decided in
docs/decisions/0007-sentence-count-abbreviations-and-ellipses.md.
"""

import re

from textkit._tokens import words


def word_count(text: str) -> int:
    """Return the number of words in ``text``, following 0002-what-counts-as-a-word.

    A word is a maximal run of letters and digits (any script), where a single hyphen or
    apostrophe between two such characters, or a "." or "," between two digits, keeps the run
    together: ``"well-known"``, ``"don't"`` and ``"3.14"`` are one word each. Everything else
    separates words, so punctuation-only or whitespace-only text has no words and
    ``word_count("") == 0``. No Unicode normalization is applied: combining marks are not
    letters, so in decomposed (NFD) text a mark inside a word splits it; normalize to NFC
    first when that matters.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        # re would accept some non-str objects with a confusing message; be explicit.
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(words(text))


def char_freq(text: str) -> dict[str, int]:
    """Return how many times each non-whitespace character occurs in ``text``.

    Counting is case-sensitive (``"a"`` and ``"A"`` are different keys) and works on code
    points: no Unicode normalization is applied, so a decomposed (NFD) ``"é"`` counts as
    ``"e"`` plus a combining accent. Characters for which ``str.isspace()`` is true (spaces,
    tabs, newlines, non-breaking spaces and other Unicode whitespace) are not counted. Keys
    appear in order of first occurrence; ``char_freq("")`` and whitespace-only text give
    ``{}``.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        # Iterating bytes or a list would "work" and return nonsense keys; be explicit.
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    # A plain dict rather than collections.Counter: the return type is promised as dict, and
    # dicts keep insertion order, which gives "order of first occurrence" for free.
    counts: dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


def reading_time(text: str, wpm: int = 200) -> int:
    """Return the minutes needed to read ``text`` at ``wpm`` words per minute.

    Words are counted with ``word_count`` (docs/decisions/0002-what-counts-as-a-word.md) and
    the result is rounded **up** to whole minutes, as decided in
    docs/decisions/0006-reading-time-rounding.md: text with no words takes ``0`` minutes, and
    any text with at least one word takes at least ``1`` minute
    (``reading_time("one word") == 1``, ``reading_time(" ".join(["w"] * 201)) == 2``).

    Raises ``TypeError`` if ``text`` is not a ``str`` or ``wpm`` is not an ``int`` (``bool``
    is rejected too), and ``ValueError`` if ``wpm < 1``.
    """
    # bool is a subclass of int; reading_time(text, True) is almost certainly a mistake.
    if isinstance(wpm, bool) or not isinstance(wpm, int):
        raise TypeError(f"reading_time() expects an int wpm, got {type(wpm).__name__}")
    if wpm < 1:
        raise ValueError(f"reading_time() needs wpm >= 1, got {wpm}")
    # Ceiling division in integers: exact for any size, unlike math.ceil on a float quotient.
    return -(-word_count(text) // wpm)


# Sentence rule: docs/decisions/0007-sentence-count-abbreviations-and-ellipses.md.
# A candidate end is a whitespace-delimited chunk ending in a run of terminators, optionally
# followed by closing quotes or brackets, and then whitespace or the end of the text. The
# chunk before the run is captured so that abbreviations can be recognised; (?<!\S) anchors
# the match at the start of the chunk so the capture is the whole chunk.
# The terminator run is anchored to be maximal ((?<![.!?…]) before it, (?![.!?…]) after
# it). Without that, a long run not followed by whitespace ("." * 8000 + "x") is retried
# at every split between the lazy chunk and the run, which is quadratic. The anchors do not
# change any result: a run can only be followed by a closer, whitespace or the end, never
# by another terminator, so only the maximal run could ever match.
_SENTENCE_END = re.compile(
    r"(?<!\S)(\S*?)(?<![.!?…])([.!?…]+)(?![.!?…])([\"'”’»)\]}]*)(?=\s|$)"
)

# Abbreviations whose final "." never ends a sentence, compared lower-cased and without the
# final ".". Dotted single letters ("e.g", "i.e", "U.S", initials such as "J") are handled by
# _INITIALS instead of being listed.
_ABBREVIATIONS = frozenset(
    {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "cf"}
)
_INITIALS = re.compile(r"[^\W\d_](?:\.[^\W\d_])*")

# After an ellipsis, the first letter or digit of what follows, skipping whitespace and
# opening punctuation such as quotes or brackets.
_NEXT_WORD_CHAR = re.compile(r"\s*[^\w\s]*(\w)")


def _ends_sentence(text: str, match: "re.Match[str]") -> bool:
    """Tell whether a candidate end found by ``_SENTENCE_END`` really ends a sentence."""
    chunk, run = match.group(1), match.group(2)
    if "!" in run or "?" in run:
        return True
    if "…" in run or len(run) > 1:
        # An ellipsis: a pause inside the sentence unless the next word is capitalised.
        nxt = _NEXT_WORD_CHAR.match(text, match.end())
        return nxt is None or nxt.group(1).isupper()
    # A single period: not an end after a known abbreviation or dotted single letters.
    # Leading opening punctuation is not part of the abbreviation: "(e.g." is "e.g".
    token = re.sub(r"^\W+", "", chunk)
    return not (token.lower() in _ABBREVIATIONS or _INITIALS.fullmatch(token))


def sentence_count(text: str) -> int:
    """Return the number of sentences in ``text``, following the rule in
    docs/decisions/0007-sentence-count-abbreviations-and-ellipses.md.

    A sentence ends at a run of ``.``, ``!``, ``?`` or ``…`` (closing quotes and brackets may
    follow) that is followed by whitespace or the end of the text, so ``"3.14"`` and ``"e.g.,"``
    end nothing. A run with ``!`` or ``?`` always ends a sentence and counts once
    (``"Really?!"``). A single ``.`` does not end one after a common abbreviation (``Mr``,
    ``Mrs``, ``Ms``, ``Dr``, ``Prof``, ``Sr``, ``Jr``, ``St``, ``vs``, ``etc``, ``cf``, any
    case) or after dotted single letters (``e.g.``, ``i.e.``, ``U.S.``, initials such as
    ``J.``). An ellipsis (``…`` or two or more dots) ends a sentence only when the next word
    starts with an upper-case letter. Line breaks alone do not end sentences.

    Only pieces that contain at least one word (as defined for :func:`word_count`) are
    counted, so ``sentence_count("") == 0``, punctuation-only text gives 0, and text with
    words but no final terminator still counts its last sentence (``"Hello"`` is 1).

    This is a heuristic: an abbreviation or initial that really ends a sentence
    (``"... etc. Then"``) is not counted as an end.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects str, got {type(text).__name__}")
    count = 0
    start = 0
    for match in _SENTENCE_END.finditer(text):
        if _ends_sentence(text, match):
            # Pieces are disjoint slices, so the tokenizer reads each character once.
            if words(text[start:match.end()]):
                count += 1
            start = match.end()
    # The text after the last end is a sentence too when it has a word.
    if words(text[start:]):
        count += 1
    return count
