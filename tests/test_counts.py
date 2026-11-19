"""Tests for textkit.counts.

`WordCountTest` checks every row of the case table that ends ADR 0001
(docs/decisions/0001-word-rule.md), read from the ADR itself so the table and the code cannot
drift apart. `CharFreqTest` checks `char_freq` (plan task T1.6). `ReadingTimeTest` checks
every row of the case table that ends ADR 0004 (docs/decisions/0004-reading-time-rounding.md)
the same way, plus the argument checks of `reading_time` (plan task T2.1).
"""

import ast
import pathlib
import re
import unittest

from textkit.counts import _words, char_freq, reading_time, word_count

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


_ROUNDING_ADR = _ADR.with_name("0004-reading-time-rounding.md")
# A table row: | `text literal` | words | wpm | minutes | description |
_ROUNDING_ROW = re.compile(
    r"^\| `(?P<text>[^`]*)` \| (?P<words>\d+) \| (?P<wpm>\d+) \| (?P<minutes>\d+) \| .+ \|$"
)


def _rounding_cases() -> list[tuple[str, int, int, int]]:
    """Return (text, words, wpm, minutes) for every row of ADR 0004's "Cases" table."""
    text = _ROUNDING_ADR.read_text(encoding="utf-8")
    section = text.split("\n## Cases\n", 1)[1]
    return [
        (ast.literal_eval(m["text"]), int(m["words"]), int(m["wpm"]), int(m["minutes"]))
        for m in map(_ROUNDING_ROW.match, section.splitlines())
        if m
    ]


class ReadingTimeTest(unittest.TestCase):
    def test_adr_table_is_present(self):
        # The plan requires an empty text and under one minute; a parsing slip must not
        # empty the table.
        cases = _rounding_cases()
        self.assertGreaterEqual(len(cases), 10)
        self.assertIn(("", 0, 200, 0), cases)
        self.assertIn(("Hello", 1, 200, 1), cases)

    def test_every_adr_row(self):
        for text, words, wpm, minutes in _rounding_cases():
            with self.subTest(text=text, wpm=wpm):
                # The Words column documents the row; it must match ADR 0001's rule.
                self.assertEqual(word_count(text), words)
                self.assertEqual(reading_time(text, wpm), minutes)
                self.assertEqual(reading_time(text, wpm=wpm), minutes)

    def test_default_is_200_wpm(self):
        self.assertEqual(reading_time("word " * 200), 1)
        self.assertEqual(reading_time("word " * 201), 2)
        self.assertEqual(reading_time("word " * 400), 2)
        self.assertEqual(reading_time("word " * 401), 3)

    def test_returns_int(self):
        self.assertIs(type(reading_time("a b c", 2)), int)
        self.assertIs(type(reading_time("")), int)

    def test_large_counts_are_exact(self):
        # Integer ceiling division: no float error even far beyond everyday sizes.
        self.assertEqual(reading_time("w " * 600_000, 3), 200_000)
        self.assertEqual(reading_time("w " * 600_001, 3), 200_001)

    def test_wpm_below_one_raises_value_error(self):
        for wpm in [0, -1, -200]:
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("some words", wpm)

    def test_rejects_non_int_wpm(self):
        for wpm in [200.0, 0.5, True, False, "200", None]:
            with self.subTest(wpm=wpm):
                with self.assertRaises(TypeError):
                    reading_time("some words", wpm)

    def test_rejects_non_str_text(self):
        for value in [None, b"two words", ["a", "b"], 3]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    reading_time(value)


if __name__ == "__main__":
    unittest.main()
