"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import word_count

# The case table of the word-rule ADR (docs/decisions/*-word-count-what-counts-as-a-word.md),
# row by row. Kept literal here so a failure names the input; WordCountTest also checks that
# the ADR table lists exactly these rows.
WORD_COUNT_CASES = [
    ("", 0),
    ("   \n\t  ", 0),
    ("!!! ... ---", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("well-known", 1),
    ("R2-D2", 1),
    ("rock--roll", 2),
    ("a - b", 2),
    ("don't", 1),
    ("don’t", 1),
    ("'quoted' dogs'", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("end.Start", 2),
    ("a  b\n\nc\td", 4),
    ("snake_case", 2),
    ("naïve café", 2),
    ("año 2026", 2),
]


def _adr_cases() -> list:
    """Parse the ADR case table into (input, count) pairs.

    The ADR is found by its slug, not its number, because the integrator may renumber it.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-word-count-what-counts-as-a-word.md")
    text = adr.read_text(encoding="utf-8")
    table = text.split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(src), int(n)) for src, n in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    word_count(bad)


if __name__ == "__main__":
    unittest.main()
