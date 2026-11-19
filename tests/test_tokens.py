"""Tests for textkit._tokens (plan task T1.10).

WordsTest has one assertion per row of the case table that ends the word-rule ADR
(docs/decisions/0002-what-counts-as-a-word.md): the exact list of words for each input. It
also checks that its inputs and word counts stay identical to that table, so the tokenizer
cannot drift from the rule that textkit.counts.word_count is tested against.
"""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words

# One row per row of the word-rule ADR's case table, same order: (input, expected words).
ROWS = [
    ("", []),
    ("   \n\t  ", []),
    ("!!! ... ?", []),
    ("hello world", ["hello", "world"]),
    ("well-known", ["well-known"]),
    ("state-of-the-art design", ["state-of-the-art", "design"]),
    ("a - b", ["a", "b"]),
    ("a--b", ["a", "b"]),
    ("-leading and trailing-", ["leading", "and", "trailing"]),
    ("2010–2020", ["2010", "2020"]),
    ("don't", ["don't"]),
    ("O’Neill", ["O’Neill"]),
    ("the dogs' bowls", ["the", "dogs", "bowls"]),
    ("rock ’n’ roll", ["rock", "n", "roll"]),
    ("42", ["42"]),
    ("3.14 and 1,000", ["3.14", "and", "1,000"]),
    ("v2.0", ["v2.0"]),
    ("page 3.", ["page", "3"]),
    ("e.g.", ["e", "g"]),
    ("end.", ["end"]),
    ("hello,world", ["hello", "world"]),
    ("snake_case", ["snake", "case"]),
    ("one  two\n\nthree\tfour\r\n", ["one", "two", "three", "four"]),
    # NFC: precomposed letters.
    ("\xd1and\xfa caf\xe9", ["\xd1and\xfa", "caf\xe9"]),
    # NFD: the combining tilde and acute accent stay in the word they follow.
    ("Ñandú", ["Ñandú"]),
    # A combining mark with no word character before it separates.
    ("́abc", ["abc"]),
]

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _adr_rows() -> list:
    """Parse the word ADR's case table. Glob on the slug: the number may change at merge."""
    (adr,) = sorted((_ROOT / "docs" / "decisions").glob("*-what-counts-as-a-word.md"))
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordsTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in ROWS:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_rows_match_adr_table(self):
        self.assertEqual(_adr_rows(), [(text, len(expected)) for text, expected in ROWS])

    def test_rejects_non_str(self):
        for value in (None, 42, b"bytes", ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    words(value)


if __name__ == "__main__":
    unittest.main()
