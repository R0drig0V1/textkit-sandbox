"""Tests for textkit._tokens, the shared tokenizer (private module, plan task T1.10)."""

import ast
import pathlib
import re
import unittest
from unittest import mock

from textkit import _tokens
from textkit._tokens import words
from textkit.cases import to_snake_case
from textkit.counts import word_count

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The case table of the word-rule ADR (ADR 0002), row by row: the input and the words it
# gives. The ADR lists only the count; `test_cases_match_the_adr_table` checks that the inputs
# and the number of words here match it. Non-ASCII inputs are escaped so the code points
# (NFC vs NFD, U+2019, U+2014) are visible.
WORDS_CASES = [
    ("", []),
    ("hello", ["hello"]),
    ("Hello, world!", ["Hello", "world"]),
    ("  one   two \n\n three\t", ["one", "two", "three"]),
    ("!!! ... ---", []),
    ("well-known", ["well-known"]),
    ("state-of-the-art design", ["state-of-the-art", "design"]),
    ("a - b", ["a", "b"]),
    ("a--b", ["a", "b"]),
    ("-5", ["5"]),
    ("1-2", ["1-2"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("rock'n'roll", ["rock'n'roll"]),
    ("'quoted' students'", ["quoted", "students"]),
    ("e-mail's", ["e-mail's"]),
    ("42", ["42"]),
    ("3.14 and 1,000,000", ["3.14", "and", "1,000,000"]),
    ("v2.0", ["v2.0"]),
    ("U.S.A.", ["U", "S", "A"]),
    ("end. Next", ["end", "Next"]),
    ("x2 3x", ["x2", "3x"]),
    ("C++", ["C"]),
    ("snake_case", ["snake", "case"]),
    ("well—maybe", ["well", "maybe"]),
    ("naïve café", ["naïve", "café"]),
    ("naïve", ["naïve"]),
    ("́", []),
    ("日本語", ["日本語"]),
    ("\U0001f642", []),
]


def _adr_cases() -> list[tuple[str, int]]:
    """Parse the case table of the word-rule ADR (found by slug, so renumbering is safe)."""
    (adr,) = (ROOT / "docs" / "decisions").glob("*-what-counts-as-a-word.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordsTest(unittest.TestCase):
    def test_every_case_of_the_adr_table(self):
        # One assertion per row of ADR 0002's table.
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(_adr_cases(), [(text, len(ws)) for text, ws in WORDS_CASES])

    def test_words_keep_case_and_form(self):
        # No case folding and no normalization: each word is a slice of the input.
        self.assertEqual(words("ÉCOLE école"), ["ÉCOLE", "école"])

    def test_joiner_at_the_end_is_dropped(self):
        self.assertEqual(words("well- 3. don'"), ["well", "3", "don"])

    def test_unicode_hyphen_joins(self):
        self.assertEqual(words("well‐known"), ["well‐known"])

    def test_is_the_tokenizer_of_word_count(self):
        # word_count must stay len(words(text)) so that ADR 0002 lives in one place.
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), len(expected))


class WordsInToSnakeCaseTest(unittest.TestCase):
    """How `to_snake_case` (textkit/cases.py) uses `words`; its own table is in test_cases.py.

    ADR 0001 and ADR 0002 split the same way only at a single `_` between two words (after
    ADR 0001 turns `-` into `_`), so `to_snake_case` splits with `words` only when the
    identifier is exactly its words joined by single `_`, and handles it whole otherwise.
    """

    # The rows of ADR 0001's table that go through `words` (True) or not (False).
    ADR_0001_ROWS = [
        ("HTTPServer", True),
        ("parseURL2", True),
        ("camelCase", True),
        ("PascalCase", True),
        ("kebab-case", True),
        ("already_snake", True),
        ("", True),
        ("getHTTPResponse", True),
        ("HTTP2Server", True),
        ("utf8Encode", True),
        ("IOError", True),
        ("ABC", True),
        ("SCREAMING_SNAKE", True),
        ("my-HTTPServer", True),
        ("_private", False),  # ADR 0002 drops the leading `_` that ADR 0001 keeps.
        ("parseURLs", True),
    ]

    @staticmethod
    def _goes_through_words(name: str) -> bool:
        text = name.replace("-", "_")
        return "_".join(words(text)) == text

    def test_rows_of_adr_0001_that_go_through_words(self):
        for name, expected in self.ADR_0001_ROWS:
            with self.subTest(name=name):
                self.assertIs(self._goes_through_words(name), expected)

    def test_rows_match_the_adr_0001_table(self):
        (adr,) = (ROOT / "docs" / "decisions").glob("*-snake-case-word-boundaries.md")
        literals = re.findall(r"^\| `([^`]*)`[^|]*\|", adr.read_text(encoding="utf-8"), re.M)
        # The ADR writes the empty input as `""` (empty).
        names = ["" if literal == '""' else literal for literal in literals]
        self.assertEqual(names, [name for name, _ in self.ADR_0001_ROWS])

    def test_to_snake_case_calls_words(self):
        with mock.patch.object(_tokens, "words", wraps=_tokens.words) as spy:
            self.assertEqual(to_snake_case("my-HTTPServer"), "my_http_server")
        spy.assert_called_once_with("my_HTTPServer")

    def test_identifiers_where_the_rules_differ_are_unchanged(self):
        # Inputs `words` would split or trim differently from ADR 0001: they take the whole-
        # identifier path and keep the output they had before T1.10.
        cases = [
            ("__dunder__", "__dunder__"),
            ("a__b", "a__b"),
            ("trailing_", "trailing_"),
            ("-x", "_x"),
            ("with space", "with space"),
            ("x.Y", "x.y"),
            ("fooBar_baz Qux", "foo_bar_baz qux"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertFalse(self._goes_through_words(name))
                self.assertEqual(to_snake_case(name), expected)


if __name__ == "__main__":
    unittest.main()
