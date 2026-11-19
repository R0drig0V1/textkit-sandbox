"""Tests for textkit._tokens, the private word tokenizer (plan task T1.10).

``words`` must implement ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md) exactly:
WordsTest asserts the **Words** column of the ADR's case table, one assertion per row, and
checks that this test table and the ADR's table have not drifted apart.
"""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words

ADR_0002 = (pathlib.Path(__file__).resolve().parent.parent
            / "docs" / "decisions" / "0002-what-counts-as-a-word.md")

# The case table of ADR 0002, row by row: (row number, input, words). Non-ASCII characters that
# are easy to confuse are written as escapes: U+2019 typographic apostrophe, U+2013 en dash,
# U+2014 em dash, U+0308 / U+0301 combining marks (NFD rows).
WORDS_CASES = [
    (1, "", []),
    (2, "hello", ["hello"]),
    (3, "Hello, world!", ["Hello", "world"]),
    (4, "well-known", ["well-known"]),
    (5, "state-of-the-art design", ["state-of-the-art", "design"]),
    (6, "well--known", ["well", "known"]),
    (7, "a - b", ["a", "b"]),
    (8, "-5 and 5-", ["5", "and", "5"]),
    (9, "COVID-19", ["COVID-19"]),
    (10, "42", ["42"]),
    (11, "3.14", ["3.14"]),
    (12, "1,000,000", ["1,000,000"]),
    (13, "v2.0.1", ["v2.0.1"]),
    (14, "1, 2", ["1", "2"]),
    (15, "a,b", ["a", "b"]),
    (16, "don't", ["don't"]),
    (17, "O\u2019Brien", ["O\u2019Brien"]),
    (18, "rock 'n' roll", ["rock", "n", "roll"]),
    (19, "the students' books", ["the", "students", "books"]),
    (20, "e.g. this", ["e.g", "this"]),
    (21, "wait...what", ["wait", "what"]),
    (22, "snake_case", ["snake", "case"]),
    (23, "pages 10\u201320", ["pages", "10", "20"]),
    (24, "yes\u2014no", ["yes", "no"]),
    (25, "AT&T", ["AT", "T"]),
    (26, "user@example.com", ["user", "example.com"]),
    (27, "!!! ... ?", []),
    (28, "  one \n\n two\t three  ", ["one", "two", "three"]),
    (29, " \n\t ", []),
    (30, "na\u00efve caf\u00e9", ["na\u00efve", "caf\u00e9"]),
    (31, "nai\u0308ve cafe\u0301", ["nai\u0308ve", "cafe\u0301"]),
    (32, "\u0301abc", ["abc"]),
    (33, "\u0939\u093f\u0928\u094d\u0926\u0940", ["\u0939\u093f\u0928\u094d\u0926\u0940"]),
    (34, "\u6771\u4eac 2026", ["\u6771\u4eac", "2026"]),
    (35, "x\u00b2", ["x\u00b2"]),
]


def _adr_table() -> list:
    """Return ADR 0002's case table as (row, input, words) tuples, parsed from the ADR."""
    rows = re.findall(r"^\| (\d+) \| `(.*?)` \| `(.*?)` \| \d+ \|",
                      ADR_0002.read_text(encoding="utf-8"), re.M)
    return [(int(row), ast.literal_eval(text), ast.literal_eval(found))
            for row, text, found in rows]


class WordsTest(unittest.TestCase):
    def test_adr_0002_case_table(self):
        for row, text, expected in WORDS_CASES:
            with self.subTest(row=row, text=text):
                self.assertEqual(words(text), expected)

    def test_case_table_matches_the_adr(self):
        # Guards against the ADR's table and this one drifting apart (a row added, dropped or
        # edited on one side only), which would leave a row of the spec untested.
        self.assertEqual(WORDS_CASES, _adr_table())


if __name__ == "__main__":
    unittest.main()
