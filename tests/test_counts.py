"""Tests for textkit.counts, one TestCase class per public function.

WordCountTest tests every row of the case table that ends the word-rule ADR
(docs/decisions/*-what-counts-as-a-word.md) and checks that the table and CASES stay
identical, so neither can drift from the other.
"""

import ast
import pathlib
import re
import unicodedata
import unittest

from textkit.counts import word_count

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


if __name__ == "__main__":
    unittest.main()
