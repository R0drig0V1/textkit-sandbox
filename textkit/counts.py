"""Counting helpers. Every public function is listed in the README's function table.

What counts as a word is decided in docs/decisions/0001-what-counts-as-a-word.md; the
private ``_words`` below is the reference implementation of that rule, written so that the
shared tokenizer (plan task T1.10, ``textkit/_tokens.py``) can take it over unchanged.
Where a sentence ends is decided in docs/decisions/0004-where-a-sentence-ends.md; the
private ``_sentences`` below implements it and ``sentence_count`` counts its result.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterator, List

# Character classes of ADR 0001. Each character of the text is mapped to one class letter,
# and the word rule is then a plain regular expression over that class string. This keeps
# the rule exact for any Unicode input: the stdlib ``re`` cannot express "letter or
# combining mark" directly, but it can match a string of class letters.
_DIGIT = "D"  # str.isdecimal(): 0-9 and the decimal digits of other scripts
_LETTER = "L"  # str.isalnum() and not a decimal digit: letters, other numerics (2, XII)
_MARK = "M"  # Unicode general category M*: combining accents, Indic vowel signs
_JOINER = "J"  # joins two word characters: hyphens and apostrophes
_NUM_SEP = "S"  # joins two decimal digits only: "3.14", "1,000"
_OTHER = "O"  # everything else separates words: spaces, punctuation, symbols, "_"

_JOINERS = frozenset("-‐‑'’")  # hyphen-minus, hyphen, non-breaking hyphen,
# apostrophe, right single quotation mark (the typographic apostrophe)
_NUM_SEPS = frozenset(".,")

# A word starts with a letter or digit and continues with letters, digits and marks. A
# joiner continues it only when a letter or digit follows; "." or "," continues it only
# when a digit is on both sides.
_WORD = re.compile(r"[LD][LDM]*(?:(?:J[LD]|(?<=D)SD)[LDM]*)*")


def _char_class(char: str) -> str:
    """Return the ADR 0001 class letter of one character."""
    if char.isdecimal():
        return _DIGIT
    if char.isalnum():
        return _LETTER
    if unicodedata.category(char).startswith("M"):
        return _MARK
    if char in _JOINERS:
        return _JOINER
    if char in _NUM_SEPS:
        return _NUM_SEP
    return _OTHER


def _words(text: str) -> List[str]:
    """Return the words of ``text`` in order, as defined by ADR 0001."""
    classes = "".join(_char_class(char) for char in text)
    return [text[m.start() : m.end()] for m in _WORD.finditer(classes)]


def word_count(text: str) -> int:
    """Count the words in ``text`` by the rule of ADR 0001.

    A word is a run of letters, digits and combining marks (any script) that starts with a
    letter or digit. A hyphen or apostrophe between two such characters keeps the word
    together (``"well-known"``, ``"don't"``), as does ``.`` or ``,`` between two digits
    (``"3.14"``, ``"1,000"``). Everything else separates words: whitespace, other
    punctuation (dashes, ``/``, ``_``, ``@``), symbols and emoji. Scripts written without
    spaces (Chinese, Japanese) are not segmented: a run of their characters is one word.

    Returns 0 for an empty string or one with no letters or digits.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` and ``None`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"word_count() expects str, got {type(text).__name__}")
    return len(_words(text))


def char_freq(text: str) -> Dict[str, int]:
    """Count how often each non-whitespace character occurs in ``text``.

    Returns a plain ``dict`` mapping each character to its count, with keys in order of
    first appearance. Counting is case-sensitive: ``"A"`` and ``"a"`` are separate keys.
    Punctuation, digits, symbols and emoji are counted like letters.

    Whitespace is what ``str.isspace()`` says it is, the same rule ``squeeze`` and
    ``word_count`` use: ``" "``, tabs, newlines, ``"\\r"``, the no-break space (U+00A0),
    the ideographic space (U+3000) and the other Unicode spaces, plus the ASCII separator
    controls U+001C to U+001F. Zero-width characters such as U+200B are not whitespace by
    that rule and are counted.

    A "character" is one Unicode code point and the text is not normalised, so a letter
    written in two forms counts differently: NFC ``"\\u00e9"`` (é) is one key, while NFD
    ``"e\\u0301"`` (the same é) counts an ``"e"`` and a combining acute accent. Normalise first
    (``unicodedata.normalize("NFC", text)``) to count the composed forms together. This
    function does not normalise because that would report characters the input never had.

    Returns ``{}`` for an empty string or one made only of whitespace.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` and ``None`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"char_freq() expects str, got {type(text).__name__}")
    counts: Dict[str, int] = {}
    for char in text:
        if not char.isspace():
            counts[char] = counts.get(char, 0) + 1
    return counts


# Sentence rule of ADR 0004.
# Characters that can end a sentence. The CJK full-width ones end it even with no space
# after, because Chinese and Japanese put no space between sentences.
_SPACELESS_TERMINATORS = "\u3002\uff01\uff1f"  # 。 ！ ？
_TERMINATORS = (
    ".!?"
    "\u2026"  # … horizontal ellipsis
    "\u203c\u203d\u2047\u2048\u2049"  # ‼ ‽ ⁇ ⁈ ⁉
    "\u061f"  # ؟ Arabic question mark
    "\u0964\u0965"  # । ॥ Devanagari danda and double danda
    + _SPACELESS_TERMINATORS
)
# Closing quotes and brackets that may follow the terminator: 'He said "Hi." Then'.
_CLOSERS = "\"')]}\u00bb\u203a\u201d\u2019\u300d\u300f\u3011\uff09"  # » › ” ’ 」 』 】 ）
# Words that a single "." follows without ending the sentence, compared in lower case and
# without that final ".". Titles before a name, and Latin abbreviations that introduce
# something. "etc." is left out on purpose: it often does end a sentence (see the ADR).
_ABBREVIATIONS = frozenset({"mr", "mrs", "ms", "dr", "prof", "e.g", "i.e", "cf", "vs"})

_ENDING = re.compile(f"([{re.escape(_TERMINATORS)}]+)([{re.escape(_CLOSERS)}]*)")
# A blank line (two line breaks with only whitespace between) or U+2029 ends a paragraph,
# and so the sentence in it. A single line break does not: prose is often hard-wrapped.
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n|\u2029")
# A letter or digit: what starts a word in ADR 0001. ``\w`` is ``str.isalnum()`` plus "_".
_ALNUM = re.compile(r"[^\W_]")


def _token_before(text: str, pos: int) -> str:
    """Return the run of non-whitespace before ``pos``, without leading punctuation."""
    start = pos
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while start < pos and not text[start].isalnum():
        start += 1  # drop an opening quote or bracket: "(e.g." is "e.g"
    return text[start:pos]


def _sentence_ends(paragraph: str) -> Iterator[int]:
    """Yield the index just past each sentence end in ``paragraph`` (ADR 0004, steps 1-4)."""
    next_alnum = -1  # cached position of the next letter or digit, so the scan stays linear
    for match in _ENDING.finditer(paragraph):
        run, end = match.group(1), match.end()
        # 1. Whitespace or the end of the text must follow, except after a CJK terminator.
        #    This keeps "3.14", "v1.2.3" and "wait...what" whole.
        if end < len(paragraph) and not paragraph[end].isspace():
            if not any(char in _SPACELESS_TERMINATORS for char in run):
                continue
        # 2. A single "." after a known abbreviation does not end a sentence: "Dr. Smith".
        if run == "." and _token_before(paragraph, match.start()).lower() in _ABBREVIATIONS:
            continue
        # 3. If the next letter is lower case, the sentence goes on: "Wait... what?",
        #    '"Hi!" she said', "etc. and more".
        if next_alnum < end:
            found = _ALNUM.search(paragraph, end)
            next_alnum = found.start() if found else len(paragraph)
        if next_alnum < len(paragraph) and paragraph[next_alnum].islower():
            continue
        yield end


def _sentences(text: str) -> List[str]:
    """Return the sentences of ``text`` in order, stripped of surrounding whitespace.

    Sentences are split as ADR 0004 says; a piece with no letter or digit (``"..."``,
    ``"!!!"``) is not a sentence and is left out.
    """
    sentences = []
    for paragraph in _PARAGRAPH_BREAK.split(text):
        start = 0
        for end in [*_sentence_ends(paragraph), len(paragraph)]:
            if _ALNUM.search(paragraph, start, end):
                sentences.append(paragraph[start:end].strip())
            start = end
    return sentences


def sentence_count(text: str) -> int:
    """Count the sentences in ``text`` by the rule of ADR 0004.

    A sentence ends at a run of terminators (``.``, ``!``, ``?``, ``…`` and the others the
    ADR lists, so ``"?!"`` and ``"..."`` end one sentence, not several), optionally followed
    by closing quotes or brackets, when whitespace or the end of the text comes next. A CJK
    full stop, ``！`` or ``？`` ends a sentence even with no space after it. A terminator does
    not end the sentence when:

    - no whitespace follows it, so decimals and versions stay whole (``"3.14"``);
    - it is a single ``.`` after ``Mr``, ``Mrs``, ``Ms``, ``Dr``, ``Prof``, ``e.g``, ``i.e``,
      ``cf`` or ``vs`` (any case);
    - the next letter is lower case (``"Wait... what?"``, ``'"Hi!" she said.'``).

    A blank line or U+2029 also ends a sentence; a single line break does not. Text after
    the last terminator is a sentence too, so ``"No full stop"`` counts 1. Only pieces with
    at least one letter or digit count, so ``""``, whitespace and ``"...!?"`` give 0.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` and ``None`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"sentence_count() expects str, got {type(text).__name__}")
    return len(_sentences(text))
