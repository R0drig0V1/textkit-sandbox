"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import word_count

# The table of cases at the end of the word-rule ADR, row by row (input, count). Kept as
# code so the cases are readable here; `test_cases_match_the_adr_table` keeps both in sync.
WORD_COUNT_CASES = [
    ("", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("  one   two \n\n three\t", 3),
    ("!!! ... ---", 0),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("a--b", 2),
    ("-5", 1),
    ("1-2", 1),
    ("don't", 1),
    ("don’t", 1),
    ("rock'n'roll", 1),
    ("'quoted' students'", 2),
    ("e-mail's", 1),
    ("42", 1),
    ("3.14 and 1,000,000", 3),
    ("v2.0", 1),
    ("U.S.A.", 3),
    ("end. Next", 2),
    ("x2 3x", 2),
    ("C++", 1),
    ("snake_case", 2),
    ("well—maybe", 2),
    ("naïve café", 2),
    ("naïve", 1),
    ("́", 0),
    ("日本語", 1),
    ("\U0001f642", 0),
]


def _adr_cases() -> list[tuple[str, int]]:
    """Parse the case table of the word-rule ADR (found by slug, so renumbering is safe)."""
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-what-counts-as-a-word.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordCountTest(unittest.TestCase):
    def test_every_case_of_the_adr_table(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_rejects_non_str(self):
        for value in (None, b"two words", ["a", "b"], 3):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
