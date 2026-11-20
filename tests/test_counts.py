"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import word_count

# Every row of the case table in ADR 0002 (what counts as a word), in the same order.
WORD_COUNT_CASES = [
    ("", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("a--b", 2),
    ("-dash- start", 2),
    ("a—b", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("-5", 1),
    ("$5 or 5%", 3),
    ("Chapter 1.", 2),
    ("1, 2, 3", 3),
    ("v1.2", 1),
    ("hello123", 1),
    ("don't", 1),
    ("don’t", 1),
    ("rock'n'roll", 1),
    ("the students' books", 3),
    ("'quoted'", 1),
    ("e.g.", 2),
    ("example.com", 2),
    ("snake_case", 2),
    ("camelCase", 1),
    ("naïve café", 2),
    ("Ñandú", 1),
    ("́", 0),
    ("日本語", 1),
    ("!!! ... ?", 0),
    (" \n\t ", 0),
    ("  a \n\n b\t c  ", 3),
]


def _adr_cases() -> list:
    """Parse the case table of the word ADR (found by title, so renumbering does not break it)."""
    root = pathlib.Path(__file__).resolve().parents[1]
    (adr,) = (root / "docs" / "decisions").glob("*-what-counts-as-a-word.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(text), int(count)) for text, count in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_adr_table(self):
        # Keeps "tests every row" true when the ADR table changes.
        self.assertEqual(WORD_COUNT_CASES, _adr_cases())

    def test_nfc_and_nfd_agree(self):
        self.assertEqual(word_count("Ñandú"), word_count("Ñandú"))

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            word_count(["a", "b"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
