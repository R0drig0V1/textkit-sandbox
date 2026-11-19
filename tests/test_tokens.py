"""Tests for textkit._tokens, the private tokenizer shared by word_count and to_snake_case."""

import re
import unittest

from tests.test_cases import ADR_0001_CASES
from tests.test_counts import ADR_0002_CASES
from textkit._tokens import words

# The table of cases at the end of docs/decisions/0002-what-counts-as-a-word.md, row by row
# and in the same order, with the words each input splits into (the table gives their count).
# Keep the two in sync, as tests/test_counts.py's ADR_0002_CASES is.
ADR_0002_WORDS = [
    ("well-known", ["well-known"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000", ["1,000,000"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("the dogs' bowls", ["the", "dogs", "bowls"]),
    ("'tis", ["tis"]),
    ("", []),
    ("!!! ... ?", []),
    ("  one \n\n two\t three  ", ["one", "two", "three"]),
    ("a--b", ["a", "b"]),
    ("well - known", ["well", "known"]),
    ("snake_case", ["snake", "case"]),
    ("U.S.A.", ["U", "S", "A"]),
    ("1, 2, 3", ["1", "2", "3"]),
    ("naïve café", ["naïve", "café"]),
    # NFD: "i" + U+0308 and "e" + U+0301, written as escapes so editors cannot compose them.
    ("nai\u0308ve cafe\u0301", ["nai\u0308ve", "cafe\u0301"]),
]


class WordsTest(unittest.TestCase):
    def test_adr_0002_table(self):
        for text, expected in ADR_0002_WORDS:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_table_matches_word_count_table(self):
        # Same inputs, same order and the same counts as the table tests/test_counts.py checks.
        self.assertEqual(
            [(text, len(expected)) for text, expected in ADR_0002_WORDS], ADR_0002_CASES
        )

    def test_trailing_joiner_is_not_part_of_the_word(self):
        self.assertEqual(words("pre-"), ["pre"])
        self.assertEqual(words("3."), ["3"])

    def test_words_are_slices_of_the_input(self):
        # No case change and no normalization: "É" and the NFD "e" + U+0301 stay as given.
        self.assertEqual(words("Été e\u0301te"), ["Été", "e\u0301te"])

    def test_mark_with_no_word_before_it_separates(self):
        self.assertEqual(words("\u0301a _\u0301"), ["a"])

    def test_agrees_with_adr_0001_separators_where_to_snake_case_uses_it(self):
        # to_snake_case takes its chunks from words() only for names made of alphanumerics
        # and "_"; for those, words() must cut exactly as ADR 0001's separator rule does.
        for name, _ in ADR_0001_CASES:
            if all(ch.isalnum() or ch == "_" for ch in name):
                with self.subTest(name=name):
                    expected = [chunk for chunk in re.split(r"[-_]+", name) if chunk]
                    self.assertEqual(words(name), expected)
