"""Tests for textkit.counts.

`WordCountTest` checks every row of the case table that ends ADR 0001
(docs/decisions/0001-word-rule.md), read from the ADR itself so the table and the code cannot
drift apart. `CharFreqTest` checks `char_freq` (plan task T1.6).
"""

import ast
import pathlib
import re
import unittest

from textkit.counts import _words, char_freq, word_count

_ADR = pathlib.Path(__file__).resolve().parents[1] / "docs" / "decisions" / "0001-word-rule.md"
# A table row: | `input literal` | count | `words literal` | description |
_ROW = re.compile(r"^\| `(?P<input>[^`]*)` \| (?P<count>\d+) \| `(?P<words>[^`]*)` \| .+ \|$")


def _adr_cases() -> list[tuple[str, int, list[str]]]:
    """Return (input, count, words) for every row of the ADR's "Cases" table."""
    text = _ADR.read_text(encoding="utf-8")
    section = text.split("\n## Cases\n", 1)[1]
    return [
        (ast.literal_eval(m["input"]), int(m["count"]), ast.literal_eval(m["words"]))
        for m in map(_ROW.match, section.splitlines())
        if m
    ]


class WordCountTest(unittest.TestCase):
    def test_adr_table_is_present(self):
        # The plan requires these kinds of rows; a parsing slip must not empty the table.
        inputs = [case[0] for case in _adr_cases()]
        for required in ["", "well-known", "42", "don't", "...", "a  b\n\nc\td"]:
            self.assertIn(required, inputs)

    def test_every_adr_row(self):
        for text, count, words in _adr_cases():
            with self.subTest(text=text):
                self.assertEqual(word_count(text), count)
                # The Words column is the contract T1.10's `words` must keep.
                self.assertEqual(_words(text), words)
                self.assertEqual(len(words), count)

    def test_rejects_non_str(self):
        for value in [None, b"two words", ["a", "b"], 3]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_is_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_skips_every_isspace_character(self):
        # Space, tab, newline, carriage return, form feed, no-break space, ideographic space.
        self.assertEqual(char_freq("a b\tc\nd\re\ff\u00a0g\u3000h"),
                         {c: 1 for c in "abcdefgh"})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("cabbac")), ["c", "a", "b"])

    def test_counts_punctuation_digits_and_non_ascii(self):
        self.assertEqual(char_freq("¡Sí! 1,1"), {"¡": 1, "S": 1, "í": 1, "!": 1, "1": 2, ",": 1})

    def test_counts_code_points_without_normalization(self):
        # NFD "é" is "e" plus a combining acute accent: two keys.
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n "), {})

    def test_rejects_non_str(self):
        for value in [None, b"abc", ["a", "b"], 3]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)


if __name__ == "__main__":
    unittest.main()
