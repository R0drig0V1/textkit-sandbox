"""Tests for the private shared tokenizer textkit._tokens (plan task T1.10).

``words`` is checked against the example table of ADR 0001, the same table that
tests/test_counts.py runs through ``word_count``. ``char_class`` is checked on each class.

T1.10 had to move the word rule out of ``textkit.counts`` and the character classification
out of ``textkit.cases`` with no change in any result (``to_camel_case`` and
``to_kebab_case``, built on ``to_snake_case``, included). To prove that, this file keeps
frozen copies of the code as it was before the move (``_old_*`` below, copied verbatim
apart from names and comments) and compares the new code with them: per character over the
whole Unicode range, and per string on the ADR tables (NFC and NFD) plus a large seeded
random sample of strings built from the characters the rules care about. The frozen copies
must never be "fixed": if a test here fails, the refactor changed behaviour.
"""

import random
import re
import sys
import unicodedata
import unittest
from typing import List

from tests.test_cases import _adr_examples as snake_examples
from tests.test_counts import adr_examples as word_examples
from textkit import _tokens
from textkit._tokens import DIGIT, JOINER, LETTER, MARK, NUM_SEP, OTHER, char_class, words
from textkit.cases import to_camel_case, to_kebab_case, to_snake_case
from textkit.counts import word_count

# --- Frozen pre-T1.10 code: textkit/counts.py ----------------------------------------------

_OLD_JOINERS = frozenset("-‐‑'’")
_OLD_NUM_SEPS = frozenset(".,")
_OLD_WORD = re.compile(r"[LD][LDM]*(?:(?:J[LD]|(?<=D)SD)[LDM]*)*")


def _old_char_class(char: str) -> str:
    if char.isdecimal():
        return "D"
    if char.isalnum():
        return "L"
    if unicodedata.category(char).startswith("M"):
        return "M"
    if char in _OLD_JOINERS:
        return "J"
    if char in _OLD_NUM_SEPS:
        return "S"
    return "O"


def _old_words(text: str) -> List[str]:
    classes = "".join(_old_char_class(char) for char in text)
    return [text[m.start() : m.end()] for m in _OLD_WORD.finditer(classes)]


# --- Frozen pre-T1.10 code: textkit/cases.py -----------------------------------------------


def _old_is_lower(ch: str) -> bool:
    return ch.isalpha() and not ch.isupper()


def _old_is_mark(ch: str) -> bool:
    return unicodedata.category(ch).startswith("M")


def _old_next_base(name: str, start: int) -> str:
    for ch in name[start:]:
        if not _old_is_mark(ch):
            return ch
    return ""


def _old_to_snake_case(name: str) -> str:
    words_: List[str] = []
    current: List[str] = []

    def flush() -> None:
        if current:
            words_.append("".join(current))
            current.clear()

    for i, ch in enumerate(name):
        if _old_is_mark(ch):
            if current:
                current.append(ch)
            continue
        if not ch.isalnum():
            flush()
            continue
        if current and ch.isupper():
            prev = next(c for c in reversed(current) if not _old_is_mark(c))
            nxt = _old_next_base(name, i + 1)
            if not prev.isupper():
                flush()
            elif _old_is_lower(nxt):
                flush()
        current.append(ch)
    flush()

    return "_".join(word.lower() for word in words_)


def _old_to_camel_case(name: str) -> str:
    words_ = _old_to_snake_case(name).split("_")
    return words_[0] + "".join(word.capitalize() for word in words_[1:])


def _old_to_kebab_case(name: str) -> str:
    return _old_to_snake_case(name).replace("_", "-")


# --- Sample --------------------------------------------------------------------------------

# Pieces the rules treat differently: cases, digits of two scripts, other numerics, CJK,
# composed and decomposed accents, a stray spacing mark, every joiner and number
# separator, "_", spaces, other punctuation, symbols and emoji, plus acronym-like runs.
_PIECES = [
    "a", "z", "A", "Z", "é", "É", "é", "É", "́", "ि", "ß", "ǅ",
    "0", "7", "٢", "²", "Ⅻ", "日", "の", "-", "‐", "‑", "'", "’", ".", ",", "_", " ",
    "\t", " ", "–", "—", "/", "@", "$", "%", "+", "\U0001f44b",
    "HTTP", "Server", "url", "ID", "v2",
]


def _sample(count: int = 20000, seed: int = 1010) -> List[str]:
    """Seeded random strings of 0 to 10 pieces: the same sample on every run."""
    rng = random.Random(seed)
    return ["".join(rng.choice(_PIECES) for _ in range(rng.randint(0, 10))) for _ in range(count)]


def _fixed_inputs() -> List[str]:
    """Every input of the ADR 0001 and ADR 0002 tables, in NFC and NFD."""
    texts = [text for text, _, _ in word_examples()] + [src for src, _ in snake_examples()]
    return [unicodedata.normalize(form, t) for t in texts for form in ("NFC", "NFD")]


class WordsTest(unittest.TestCase):
    def test_adr_0001_table(self):
        examples = word_examples()
        self.assertGreaterEqual(len(examples), 40)  # the table parser matched rows
        for text, expected, _ in examples:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_adr_0001_table_in_nfd(self):
        # A mark continues its word, so decomposing the input decomposes the words only.
        for text, expected, _ in word_examples():
            nfd = unicodedata.normalize("NFD", text)
            with self.subTest(text=text):
                self.assertEqual(words(nfd), [unicodedata.normalize("NFD", w) for w in expected])

    def test_words_are_slices_of_the_text(self):
        text = "Don't SHOUT: 3.14-ish café"
        self.assertEqual(words(text), ["Don't", "SHOUT", "3.14-ish", "café"])

    def test_pattern_is_the_one_printed_in_adr_0001(self):
        self.assertEqual(_tokens._WORD.pattern, r"[LD][LDM]*(?:(?:J[LD]|(?<=D)SD)[LDM]*)*")


class CharClassTest(unittest.TestCase):
    def test_each_class(self):
        cases = {
            DIGIT: "07٢",
            LETTER: "aZéß日²Ⅻ",
            MARK: "́ि⃝",
            JOINER: "-‐‑'’",
            NUM_SEP: ".,",
            OTHER: " \t_–—/@$%+\U0001f44b",
        }
        for cls, chars in cases.items():
            for ch in chars:
                with self.subTest(char=ch):
                    self.assertEqual(char_class(ch), cls)


class NoBehaviourChangeTest(unittest.TestCase):
    """The T1.10 refactor against frozen copies of the code it replaced."""

    def test_char_class_matches_old_code_on_every_code_point(self):
        for cp in range(sys.maxunicode + 1):
            ch = chr(cp)
            new = char_class(ch)
            if new != _old_char_class(ch):
                self.fail(f"char_class changed for U+{cp:04X}")
            # to_snake_case used to test "mark" first, then "not alnum"; char_class tests
            # alnum first. Both orders agree only because no character is both a mark and
            # alphanumeric, which this checks for the running Python's Unicode data.
            old_snake = "mark" if _old_is_mark(ch) else ("word" if ch.isalnum() else "sep")
            new_snake = "mark" if new == MARK else ("word" if new in (LETTER, DIGIT) else "sep")
            if new_snake != old_snake:
                self.fail(f"to_snake_case classification changed for U+{cp:04X}")

    def test_words_and_word_count_match_old_code(self):
        for text in _fixed_inputs() + _sample():
            old = _old_words(text)
            if words(text) != old or word_count(text) != len(old):
                self.fail(f"words changed for {text!r}")

    def test_to_snake_case_matches_old_code(self):
        for name in _fixed_inputs() + _sample():
            if to_snake_case(name) != _old_to_snake_case(name):
                self.fail(f"to_snake_case changed for {name!r}")

    def test_to_camel_case_matches_old_code(self):
        # to_camel_case is built on to_snake_case, so it must not change either.
        for name in _fixed_inputs() + _sample():
            if to_camel_case(name) != _old_to_camel_case(name):
                self.fail(f"to_camel_case changed for {name!r}")

    def test_to_kebab_case_matches_old_code(self):
        # to_kebab_case is built on to_snake_case, so it must not change either.
        for name in _fixed_inputs() + _sample():
            if to_kebab_case(name) != _old_to_kebab_case(name):
                self.fail(f"to_kebab_case changed for {name!r}")


if __name__ == "__main__":
    unittest.main()
