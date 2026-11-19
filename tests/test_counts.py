"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, reading_time, word_count

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


READING_TIME_ADR = ADR.parent / "0004-reading-time-rounding.md"

# The case table of ADR 0004, row by row, in the same order: (words, wpm, minutes).
READING_TIME_CASES = [
    (0, 200, 0),
    (0, 1, 0),
    (1, 200, 1),
    (199, 200, 1),
    (200, 200, 1),
    (201, 200, 2),
    (400, 200, 2),
    (401, 200, 3),
    (5, 1, 5),
    (1, 1000, 1),
]


def _reading_time_adr_cases() -> list[tuple[int, int, int]]:
    """Parse the "Cases" table of ADR 0004 into (words, wpm, minutes) triples."""
    section = READING_TIME_ADR.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| (\d+) \| (\d+) \| (\d+) \|", section, re.M)
    return [(int(words), int(wpm), int(minutes)) for words, wpm, minutes in rows]


def _text_of(words: int) -> str:
    """Return a text that word_count counts as exactly ``words`` words."""
    return " ".join(["word"] * words)


class ReadingTimeTest(unittest.TestCase):
    def test_every_case_of_the_adr(self):
        for words, wpm, minutes in READING_TIME_CASES:
            with self.subTest(words=words, wpm=wpm):
                text = _text_of(words)
                self.assertEqual(word_count(text), words)
                self.assertEqual(reading_time(text, wpm), minutes)

    def test_cases_match_the_adr_table(self):
        # Keeps the ADR and this list from drifting apart: the ADR is the specification.
        self.assertEqual(_reading_time_adr_cases(), READING_TIME_CASES)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time(_text_of(200)), 1)
        self.assertEqual(reading_time(_text_of(201)), 2)

    def test_text_with_no_words_takes_zero_minutes(self):
        for text in ("", "   \n\t ", "!!! ... ?"):
            with self.subTest(text=text):
                self.assertEqual(reading_time(text), 0)

    def test_counts_words_with_word_count(self):
        # "well-known" is one word and "C++" one word under ADR 0001: 2 words, not 4 tokens.
        self.assertEqual(reading_time("well-known C++", wpm=2), 1)
        self.assertEqual(reading_time("well-known C++", wpm=1), 2)

    def test_returns_int(self):
        self.assertIs(type(reading_time(_text_of(3), 2)), int)

    def test_rejects_wpm_below_one(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("hello", wpm)

    def test_rejects_non_int_wpm(self):
        for wpm in (200.0, 0.5, "200", None, True):
            with self.subTest(wpm=wpm):
                with self.assertRaises(TypeError):
                    reading_time("hello", wpm)

    def test_rejects_non_str_text(self):
        for value in (None, b"hello world", 42):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    reading_time(value)


if __name__ == "__main__":
    unittest.main()
