"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import word_count

# The case table of docs/decisions/0002-what-counts-as-a-word.md, as (input, count). The ADR
# is the specification; WordCountTest.test_adr_table_matches keeps the two in sync.
WORD_COUNT_CASES = [
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("foo--bar", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000 people", 2),
    ("2nd place", 2),
    ("don't", 1),
    ("it’s", 1),
    ("'quoted'", 1),
    ("the dogs' bowls", 3),
    ("", 0),
    ("!?.,;:--", 0),
    ("   \n\t  ", 0),
    ("one  two\n\nthree\tfour", 4),
    ("end.Start", 2),
    ("already_snake", 2),
    ("naïve café", 2),
    ("naïve", 2),
]

_DECISIONS = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions"


def _adr_cases() -> list:
    """Parse the case table of the word ADR into (input, count) pairs.

    Found by title rather than number, since the integrator may renumber the ADR at merge.
    """
    (adr,) = _DECISIONS.glob("*-what-counts-as-a-word.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_adr_table_matches(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_prose(self):
        self.assertEqual(word_count("Hello, world! It's a well-known fact."), 6)

    def test_non_str_raises_type_error(self):
        for value in (None, 42, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)


if __name__ == "__main__":
    unittest.main()
