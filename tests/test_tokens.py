"""Tests for textkit._tokens, the private shared tokenizer (plan task T1.10)."""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words

# One entry per row of the case table of docs/decisions/0002-what-counts-as-a-word.md, as
# (input, expected words). The ADR gives counts; the word lists here are what those counts
# are made of. WordsTest.test_adr_table_matches keeps inputs and counts in sync with the ADR.
WORDS_CASES = [
    ("well-known", ["well-known"]),
    ("state-of-the-art design", ["state-of-the-art", "design"]),
    ("a - b", ["a", "b"]),
    ("foo--bar", ["foo", "bar"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000 people", ["1,000", "people"]),
    ("2nd place", ["2nd", "place"]),
    ("don't", ["don't"]),
    ("it’s", ["it’s"]),
    ("'quoted'", ["quoted"]),
    ("the dogs' bowls", ["the", "dogs", "bowls"]),
    ("", []),
    ("!?.,;:--", []),
    ("   \n\t  ", []),
    ("one  two\n\nthree\tfour", ["one", "two", "three", "four"]),
    ("end.Start", ["end", "Start"]),
    ("already_snake", ["already", "snake"]),
    ("naïve café", ["naïve", "café"]),
    # NFD: the combining diaeresis after "i" is not a letter, so it splits the word.
    ("nai\u0308ve", ["nai", "ve"]),
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


class WordsTest(unittest.TestCase):
    def test_adr_cases(self):
        # One assertion per ADR row.
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_adr_table_matches(self):
        self.assertEqual(_adr_cases(), [(text, len(ws)) for text, ws in WORDS_CASES])

    def test_returns_list(self):
        self.assertIsInstance(words("a b"), list)

    def test_non_str_raises_type_error(self):
        for value in (None, 42, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    words(value)


if __name__ == "__main__":
    unittest.main()
