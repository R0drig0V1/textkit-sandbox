"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import char_freq, word_count

# Every row of the case table in docs/decisions/0001-what-counts-as-a-word.md, in the same
# order and with the same literals. Keep the two in sync: T1.10 tests its tokenizer against
# the same table.
WORD_COUNT_CASES = [
    ("", 0),
    ("  \n\t  ", 0),
    ("... !!! ?", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("one  two\n\nthree\tfour", 4),
    ("well-known", 1),
    ("state-of-the-art", 1),
    ("well - known", 2),
    ("-leading trailing-", 2),
    ("a--b", 2),
    ("word—word", 2),
    ("don't", 1),
    ("don’t", 1),
    ("rock'n'roll", 1),
    ("'quoted'", 1),
    ("dogs' bowls", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("1, 2, 3", 3),
    ("v2.0", 1),
    ("end.Start", 2),
    ("e.g.", 2),
    ("snake_case", 2),
    ("naïve café", 2),
    ("Ñandú", 1),
    ("日本語", 1),
    ("C++ and C#", 3),
    ("50%", 1),
    ("-5", 1),
]


class WordCountTest(unittest.TestCase):
    def test_adr_0001_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_nfc_and_nfd_count_the_same(self):
        # Rule 2 of ADR 0001: combining marks must not split a word.
        self.assertEqual(word_count("Ñandú es"), word_count("Ñandú es"))

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            word_count(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            word_count(["a", "b"])  # type: ignore[arg-type]


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("hello"), {"h": 1, "e": 1, "l": 2, "o": 1})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n\r\f\v\u00a0\u2003"), {})

    def test_whitespace_is_not_counted(self):
        self.assertEqual(char_freq("a b\tc\na\u00a0b"), {"a": 2, "b": 2, "c": 1})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("banana split")), ["b", "a", "n", "s", "p", "l", "i", "t"])

    def test_punctuation_digits_and_non_ascii_are_counted(self):
        self.assertEqual(char_freq("ñ1!ñ"), {"ñ": 2, "1": 1, "!": 1})

    def test_no_normalization(self):
        # NFD "ú" is two code points: "u" and U+0301 COMBINING ACUTE ACCENT.
        self.assertEqual(char_freq("u\u0301"), {"u": 1, "\u0301": 1})
        self.assertEqual(char_freq("\u00fa"), {"\u00fa": 1})

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            char_freq(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            char_freq(["a"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
