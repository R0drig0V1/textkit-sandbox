"""Tests for textkit._tokens (the private shared tokenizer). One TestCase class per function."""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words

# The case table of the word-rule ADR (docs/decisions/*-word-count-what-counts-as-a-word.md),
# row by row and in the same order, with the words each input must produce. The ADR table
# gives only counts; WordsTest checks that these rows are exactly the ADR's inputs and that
# each list has the ADR's count, so the token lists cannot drift from the table.
WORDS_CASES = [
    ("", []),
    ("   \n\t  ", []),
    ("!!! ... ---", []),
    ("hello", ["hello"]),
    ("Hello, world!", ["Hello", "world"]),
    ("well-known", ["well-known"]),
    ("R2-D2", ["R2-D2"]),
    ("rock--roll", ["rock", "roll"]),
    ("a - b", ["a", "b"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("'quoted' dogs'", ["quoted", "dogs"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000", ["1,000,000"]),
    ("end.Start", ["end", "Start"]),
    ("a  b\n\nc\td", ["a", "b", "c", "d"]),
    ("snake_case", ["snake", "case"]),
    ("naïve café", ["naïve", "café"]),
    ("año 2026", ["año", "2026"]),
    ("naïve café", ["naïve", "café"]),  # NFD of "naïve café"
    ("Ñandú", ["Ñandú"]),  # NFD of "Ñandú"
    (
        "हिन्दी",  # Hindi, vowel signs are Mc/Mn marks
        ["हिन्दी"],
    ),
    ("́ a", ["a"]),  # a mark with no letter before it is not a word
]


def _adr_cases() -> list:
    """Parse the word-rule ADR case table into (input, count) pairs.

    The ADR is found by its slug, not its number, because the integrator may renumber it.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-word-count-what-counts-as-a-word.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(src), int(n)) for src, n in rows]


class WordsTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(
            [(text, len(expected)) for text, expected in WORDS_CASES], _adr_cases()
        )

    def test_returns_words_unchanged_in_order(self):
        # No case folding or normalization: the words are slices of the input.
        self.assertEqual(words("Zeta, ALPHA beta"), ["Zeta", "ALPHA", "beta"])

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    words(bad)


if __name__ == "__main__":
    unittest.main()
