"""Tests for textkit._tokens, the shared tokenizer of ADR 0001 (plan task T1.10)."""

import ast
import pathlib
import re
import unittest

from textkit._tokens import is_word_char, words

ADR = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions" / (
    "0001-what-counts-as-a-word.md"
)

# The case table of ADR 0001, row by row, in the same order, with the words each row gives.
# The ADR states counts; the lists here pin down which words make up each count.
WORDS_CASES = [
    ("", []),
    ("   \n\t ", []),
    ("!!! ... ?", []),
    ("hello world", ["hello", "world"]),
    ("  one \n\n two\tthree  ", ["one", "two", "three"]),
    ("well-known", ["well-known"]),
    ("state-of-the-art design", ["state-of-the-art", "design"]),
    ("well--known", ["well", "known"]),
    ("pages 10 - 12", ["pages", "10", "12"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("rock 'n' roll", ["rock", "n", "roll"]),
    ("'quoted'", ["quoted"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000 people", ["1,000,000", "people"]),
    ("v1.2", ["v1.2"]),
    ("end.Next", ["end", "Next"]),
    ("a,b", ["a", "b"]),
    ("snake_case", ["snake", "case"]),
    ("C++ and C#", ["C", "and", "C"]),
    ("naïve café", ["naïve", "café"]),
    # Decomposed (NFD) as in the ADR; escaped so that no editor silently composes it.
    ("Nañdú", ["Nañdú"]),
    ("日本語", ["日本語"]),
]


def _adr_cases() -> list[tuple[str, int]]:
    """Parse the "Cases" table of ADR 0001 into (input, count) pairs."""
    section = ADR.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(\".*\")` \| (\d+) \|", section, re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordsTest(unittest.TestCase):
    # One assertion per row of the ADR 0001 table (subTest reports each row on its own).
    def test_every_case_of_the_adr(self):
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_cases_match_the_adr_table(self):
        # Same inputs, same order and the ADR's counts: the ADR is the specification.
        self.assertEqual(
            [(text, len(expected)) for text, expected in WORDS_CASES], _adr_cases()
        )

    def test_keeps_words_as_written(self):
        # No case folding and no normalization: NFD stays NFD.
        self.assertEqual(words("Café café"), ["Café", "café"])

    def test_identifiers_split_only_at_underscores(self):
        # textkit.cases._split_words relies on this: for a name made of word characters and
        # `_`, words() is exactly ADR 0002's rule 1 (cut at runs of `_`, drop empty ends).
        for name in ("HTTPServer", "already_snake", "_private", "__dunder__", "a__b",
                     "parse_URL2", "naïve_café", "café_x", "日本_語", "x_٣"):
            with self.subTest(name=name):
                self.assertEqual(words(name), [part for part in name.split("_") if part])


class IsWordCharTest(unittest.TestCase):
    def test_letters_numbers_and_marks(self):
        for ch in ("a", "Z", "ñ", "日", "7", "٣", "́"):
            with self.subTest(ch=ch):
                self.assertTrue(is_word_char(ch))

    def test_everything_else(self):
        for ch in (" ", "\t", "_", "-", "'", "’", ".", ",", "+", "#", "@", "—"):
            with self.subTest(ch=ch):
                self.assertFalse(is_word_char(ch))


if __name__ == "__main__":
    unittest.main()
