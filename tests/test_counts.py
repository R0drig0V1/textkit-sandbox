"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import word_count

# The table of cases at the end of docs/decisions/0001-what-counts-as-a-word.md, row by row
# and in the same order. Keep the two in sync.
ADR_0001_CASES = [
    ("well-known", 1),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("don't", 1),
    ("don’t", 1),
    ("the dogs' bowls", 3),
    ("'tis", 1),
    ("", 0),
    ("!!! ... ?", 0),
    ("  one \n\n two\t three  ", 3),
    ("a--b", 2),
    ("well - known", 2),
    ("snake_case", 2),
    ("U.S.A.", 3),
    ("1, 2, 3", 3),
    ("naïve café", 2),
    ("naïve café", 2),
]


class WordCountTest(unittest.TestCase):
    def test_adr_0001_table(self):
        for text, expected in ADR_0001_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_sentence(self):
        self.assertEqual(word_count("It's a well-known fact: 3.5 cats aren't 2 dogs."), 9)

    def test_joiner_at_end_of_text(self):
        self.assertEqual(word_count("pre-"), 1)
        self.assertEqual(word_count("3."), 1)


if __name__ == "__main__":
    unittest.main()
