"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, word_count

ADR = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions" / (
    "0001-what-counts-as-a-word.md"
)

# The case table of ADR 0001, row by row, in the same order.
WORD_COUNT_CASES = [
    ("", 0),
    ("   \n\t ", 0),
    ("!!! ... ?", 0),
    ("hello world", 2),
    ("  one \n\n two\tthree  ", 3),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("well--known", 2),
    ("pages 10 - 12", 3),
    ("don't", 1),
    ("don’t", 1),
    ("rock 'n' roll", 3),
    ("'quoted'", 1),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000 people", 2),
    ("v1.2", 1),
    ("end.Next", 2),
    ("a,b", 2),
    ("snake_case", 2),
    ("C++ and C#", 3),
    ("naïve café", 2),
    ("Nañdú", 1),
    ("日本語", 1),
]


def _adr_cases() -> list[tuple[str, int]]:
    """Parse the "Cases" table of ADR 0001 into (input, count) pairs."""
    section = ADR.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(\".*\")` \| (\d+) \|", section, re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordCountTest(unittest.TestCase):
    def test_every_case_of_the_adr(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_the_adr_table(self):
        # Keeps the ADR and this list from drifting apart: the ADR is the specification.
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_rejects_non_str(self):
        for value in (None, b"hello world", 42, ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_is_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_skips_whitespace(self):
        # Every character here satisfies str.isspace(), including U+00A0 and U+3000.
        self.assertEqual(char_freq(" a\tb\nc\r\x0b\x0c\u00a0\u3000"), {"a": 1, "b": 1, "c": 1})

    def test_counts_punctuation_digits_and_non_ascii(self):
        self.assertEqual(char_freq("ñ1!ñ"), {"ñ": 2, "1": 1, "!": 1})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("cabbac")), ["c", "a", "b"])

    def test_no_normalization(self):
        # NFD "é" is two code points, each counted on its own.
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \n\t "), {})

    def test_rejects_non_str(self):
        for value in (None, b"abc", 42, ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)


if __name__ == "__main__":
    unittest.main()
