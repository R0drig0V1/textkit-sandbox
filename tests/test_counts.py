"""Tests for textkit.counts, one TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, word_count

# The table of cases that ends the ADR "What counts as a word", row by row, in order.
# test_cases_match_the_adr_table keeps the two in sync.
WORD_COUNT_CASES = [
    ("", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("!!! ... ?", 0),
    ("  one \n\n two\t three  ", 3),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a -- b", 2),
    ("a--b", 2),
    ("-leading trailing-", 2),
    ("don't", 1),
    ("it’s", 1),
    ("'quoted'", 1),
    ("the dogs' bones", 3),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("-5", 1),
    ("COVID-19", 1),
    ("end.Start", 2),
    ("e.g.", 2),
    ("1/2", 2),
    ("snake_case", 2),
    ("naïve café", 2),
    ("naïve", 1),
    ("日本語", 1),
]

# Found by title, not number: the integrator may renumber the ADR at merge.
_DECISIONS = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions"
_ROW = re.compile(r"^\| `(.+)` \| (\d+) \|", re.M)


def _adr_cases() -> list[tuple[str, int]]:
    """Return the (input, count) rows of the word ADR's case table."""
    (adr,) = _DECISIONS.glob("[0-9][0-9][0-9][0-9]-what-counts-as-a-word.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    return [(ast.literal_eval(text), int(count)) for text, count in _ROW.findall(table)]


class WordCountTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_joiner_at_the_very_end(self):
        # The lookahead must not run past the end of the text.
        self.assertEqual(word_count("well-"), 1)
        self.assertEqual(word_count("3."), 1)

    def test_mixed_sentence(self):
        text = "It's a well-known fact: 3.14 isn't exactly π -- or is it?"
        self.assertEqual(word_count(text), 11)

    def test_rejects_non_str(self):
        for value in (b"two words", ["two", "words"], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)  # type: ignore[arg-type]


class CharFreqTest(unittest.TestCase):
    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n\r\f\v\u00a0\u2003\u3000"), {})

    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_whitespace_skipped_punctuation_counted(self):
        self.assertEqual(
            char_freq("a b,\tb!\n"), {"a": 1, "b": 2, ",": 1, "!": 1}
        )

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("cabbage")), ["c", "a", "b", "g", "e"])

    def test_non_ascii_per_code_point(self):
        self.assertEqual(char_freq("日本日"), {"日": 2, "本": 1})
        # No normalization: NFD "é" is "e" plus U+0301, counted separately.
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})

    def test_rejects_non_str(self):
        for value in (b"abc", ["a", "b"], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
