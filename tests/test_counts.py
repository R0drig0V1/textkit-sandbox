"""Tests for textkit.counts, one TestCase class per public function.

WordCountTest tests every row of the case table that ends the word-rule ADR
(docs/decisions/*-what-counts-as-a-word.md) and checks that the table and CASES stay
identical, so neither can drift from the other. CharFreqTest pins the T1.6 contract:
case-sensitive, str.isspace() characters skipped, keys in order of first occurrence.
ReadingTimeTest tests every row of the case table of the rounding ADR
(docs/decisions/*-reading-time-rounding.md) and checks it against READING_TIME_CASES.
"""

import ast
import pathlib
import re
import unicodedata
import unittest

from textkit.counts import char_freq, reading_time, word_count

# Mirror of the case table in docs/decisions/*-what-counts-as-a-word.md: (input, count).
CASES = [
    ("", 0),
    ("   \n\t  ", 0),
    ("!!! ... ?", 0),
    ("hello world", 2),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("a--b", 2),
    ("-leading and trailing-", 3),
    ("2010–2020", 2),
    ("don't", 1),
    ("O’Neill", 1),
    ("the dogs' bowls", 3),
    ("rock ’n’ roll", 3),
    ("42", 1),
    ("3.14 and 1,000", 3),
    ("v2.0", 1),
    ("page 3.", 2),
    ("e.g.", 2),
    ("end.", 1),
    ("hello,world", 2),
    ("snake_case", 2),
    ("one  two\n\nthree\tfour\r\n", 4),
    ("Ñandú café", 2),
    ("Ñandú", 1),
    ("́abc", 1),
]

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _adr_cases() -> list:
    """Parse the case table of the word ADR. Glob on the slug: the number may change at merge."""
    (adr,) = sorted((_ROOT / "docs" / "decisions").glob("*-what-counts-as-a-word.md"))
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), CASES)

    def test_nfc_and_nfd_agree(self):
        text = "Ñandú café naïve"
        self.assertEqual(word_count(unicodedata.normalize("NFC", text)), 3)
        self.assertEqual(word_count(unicodedata.normalize("NFD", text)), 3)

    def test_rejects_non_str(self):
        for value in (None, 42, b"bytes", ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_whitespace_not_counted(self):
        # Space, tab, newline, carriage return, no-break space, em space, line separator.
        text = "a b\tc\nd\re\u00a0f\u2003g\u2028h"
        self.assertEqual(char_freq(text), {c: 1 for c in "abcdefgh"})

    def test_punctuation_and_digits_counted(self):
        self.assertEqual(char_freq("a1!1!"), {"a": 1, "1": 2, "!": 2})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("hello world")), ["h", "e", "l", "o", "w", "r", "d"])

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n\r\u00a0"), {})

    def test_no_normalization(self):
        # NFD splits "ú" into "u" plus a combining acute accent, each counted on its own.
        self.assertEqual(char_freq(unicodedata.normalize("NFC", "ú")), {"ú": 1})
        self.assertEqual(char_freq(unicodedata.normalize("NFD", "ú")), {"u": 1, "\u0301": 1})

    def test_returns_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)

    def test_rejects_non_str(self):
        for value in (None, 42, b"bytes", ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)


# Mirror of the case table in docs/decisions/*-reading-time-rounding.md: (input, wpm, minutes).
READING_TIME_CASES = [
    ("", 200, 0),
    ("   \n\t  ", 200, 0),
    ("!!! ... ?", 200, 0),
    ("hello", 200, 1),
    ("hello world", 200, 1),
    ("one two three", 3, 1),
    ("one two three four", 3, 2),
    ("one two three four five six", 3, 2),
    ("one two three four five six seven", 3, 3),
    ("well-known don't", 1, 2),
    ("a - b", 1, 2),
    ("hello", 1, 1),
]


def _reading_time_adr_cases() -> list:
    """Parse the case table of the rounding ADR. Glob on the slug: the number may change at merge."""
    (adr,) = sorted((_ROOT / "docs" / "decisions").glob("*-reading-time-rounding.md"))
    rows = re.findall(r"^\| `(.*)` \| (\d+) \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), int(wpm), int(minutes)) for literal, wpm, minutes in rows]


class ReadingTimeTest(unittest.TestCase):
    def test_adr_table(self):
        for text, wpm, expected in READING_TIME_CASES:
            with self.subTest(text=text, wpm=wpm):
                self.assertEqual(reading_time(text, wpm), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_reading_time_adr_cases(), READING_TIME_CASES)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time(" ".join(["word"] * 200)), 1)
        self.assertEqual(reading_time(" ".join(["word"] * 201)), 2)
        self.assertEqual(reading_time(" ".join(["word"] * 400)), 2)

    def test_wpm_below_one_raises(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("hello", wpm)

    def test_rejects_non_int_wpm(self):
        for wpm in (200.0, "200", None, True):
            with self.subTest(wpm=wpm):
                with self.assertRaises(TypeError):
                    reading_time("hello", wpm)

    def test_rejects_non_str_text(self):
        for value in (None, 42, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    reading_time(value)


if __name__ == "__main__":
    unittest.main()
