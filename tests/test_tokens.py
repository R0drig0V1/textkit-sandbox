"""Tests for textkit._tokens (the shared tokenizer). One TestCase class per function.

WORDS_CASES has one row per row of the case table in ADR 0002 (what counts as a word), in
the same order, with the exact list of words instead of just their number. Non-ASCII inputs
are written as escapes so the NFC/NFD form of each one is visible.
"""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words
from textkit.cases import _SEPARATORS

WORDS_CASES = [
    ("", []),
    ("hello", ["hello"]),
    ("Hello, world!", ["Hello", "world"]),
    ("well-known", ["well-known"]),
    ("state-of-the-art design", ["state-of-the-art", "design"]),
    ("a - b", ["a", "b"]),
    ("a--b", ["a", "b"]),
    ("-dash- start", ["dash", "start"]),
    ("a—b", ["a", "b"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000", ["1,000,000"]),
    ("-5", ["5"]),
    ("$5 or 5%", ["5", "or", "5"]),
    ("Chapter 1.", ["Chapter", "1"]),
    ("1, 2, 3", ["1", "2", "3"]),
    ("v1.2", ["v1.2"]),
    ("hello123", ["hello123"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("rock'n'roll", ["rock'n'roll"]),
    ("the students' books", ["the", "students", "books"]),
    ("'quoted'", ["quoted"]),
    ("e.g.", ["e", "g"]),
    ("example.com", ["example", "com"]),
    ("snake_case", ["snake", "case"]),
    ("camelCase", ["camelCase"]),
    ("naïve café", ["naïve", "café"]),
    ("Ñandú", ["Ñandú"]),  # NFD: the marks stay in the word
    ("́", []),
    ("日本語", ["日本語"]),
    ("!!! ... ?", []),
    (" \n\t ", []),
    ("  a \n\n b\t c  ", ["a", "b", "c"]),
]


def _adr_table(slug: str, value: str) -> list:
    """Parse the case table at the end of an ADR (found by title, so renumbering is harmless)."""
    root = pathlib.Path(__file__).resolve().parents[1]
    (adr,) = (root / "docs" / "decisions").glob(f"*-{slug}.md")
    return re.findall(rf"^\| `(.*)` \| {value} \|$", adr.read_text(encoding="utf-8"), re.M)


class WordsTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_cases_match_adr_table(self):
        # Same inputs, same order and the same counts as ADR 0002, so "one assertion per
        # row" stays true when the table changes.
        rows = _adr_table("what-counts-as-a-word", r"(\d+)")
        adr = [(ast.literal_eval(text), int(count)) for text, count in rows]
        self.assertEqual([(text, len(expected)) for text, expected in WORDS_CASES], adr)

    def test_words_are_substrings_in_order(self):
        for text, _ in WORDS_CASES:
            with self.subTest(text=text):
                pos = 0
                for word in words(text):
                    found = text.find(word, pos)
                    self.assertGreaterEqual(found, 0, word)
                    pos = found + len(word)

    def test_agrees_with_snake_case_separators_on_routed_names(self):
        # to_snake_case sends names made only of letters, digits and "_" through words();
        # on those, words() must cut exactly where ADR 0001's separator rule cuts.
        names = _adr_table("to-snake-case-word-boundaries", r"`.*`")
        names = ["" if n == '""' else n for n in names]  # the table writes "" for empty
        routed = [n for n in names if all(ch.isalnum() or ch == "_" for ch in n)]
        self.assertTrue(routed)
        for name in routed:
            with self.subTest(name=name):
                self.assertEqual(words(name), [c for c in _SEPARATORS.split(name) if c])

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            words(["a", "b"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
