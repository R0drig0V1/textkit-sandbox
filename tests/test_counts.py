"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import word_count

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


if __name__ == "__main__":
    unittest.main()
