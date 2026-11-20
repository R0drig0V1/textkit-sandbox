"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, word_count

# The case table of the word-rule ADR (docs/decisions/*-word-count-what-counts-as-a-word.md),
# row by row. Kept literal here so a failure names the input; WordCountTest also checks that
# the ADR table lists exactly these rows.
WORD_COUNT_CASES = [
    ("", 0),
    ("   \n\t  ", 0),
    ("!!! ... ---", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("well-known", 1),
    ("R2-D2", 1),
    ("rock--roll", 2),
    ("a - b", 2),
    ("don't", 1),
    ("don’t", 1),
    ("'quoted' dogs'", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("end.Start", 2),
    ("a  b\n\nc\td", 4),
    ("snake_case", 2),
    ("naïve café", 2),
    ("año 2026", 2),
    ("nai\u0308ve cafe\u0301", 2),  # NFD of "naïve café"
    ("N\u0303andu\u0301", 1),  # NFD of "Ñandú"
    ("\u0939\u093f\u0928\u094d\u0926\u0940", 1),  # Hindi, vowel signs are Mc/Mn marks
    ("\u0301 a", 1),  # a mark with no letter before it is not a word
]


def _adr_cases() -> list:
    """Parse the ADR case table into (input, count) pairs.

    The ADR is found by its slug, not its number, because the integrator may renumber it.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-word-count-what-counts-as-a-word.md")
    text = adr.read_text(encoding="utf-8")
    table = text.split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(src), int(n)) for src, n in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    word_count(bad)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("hello"), {"h": 1, "e": 1, "l": 2, "o": 1})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_skips_every_isspace_character(self):
        # space, tab, newline, carriage return, vertical tab, form feed, NBSP, em space,
        # line separator, ideographic space: all have str.isspace() true.
        spaces = " \t\n\r\v\f\u00a0\u2003\u2028\u3000"
        self.assertTrue(all(ch.isspace() for ch in spaces))
        self.assertEqual(char_freq(f"a{spaces}b"), {"a": 1, "b": 1})

    def test_keys_in_order_of_first_occurrence(self):
        result = char_freq("banana split")
        self.assertEqual(list(result), ["b", "a", "n", "s", "p", "l", "i", "t"])
        self.assertEqual(result["a"], 3)
        self.assertEqual(result["n"], 2)

    def test_punctuation_and_digits_are_counted(self):
        self.assertEqual(char_freq("a1!a1!"), {"a": 2, "1": 2, "!": 2})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq("  \n\t "), {})

    def test_code_points_without_normalization(self):
        # NFD "é" is "e" plus a combining acute accent: two code points, two keys.
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})

    def test_returns_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3, ["a"]):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    char_freq(bad)


if __name__ == "__main__":
    unittest.main()
