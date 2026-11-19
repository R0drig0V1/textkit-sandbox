"""Tests for textkit._tokens, the shared tokenizer (plan task T1.10).

`WORDS_CASES` is the table of cases at the end of the ADR "What counts as a word" (0001),
row by row and in order, with the words each input splits into; the count column of the
ADR is the length of each list. test_cases_match_the_adr_table keeps the two in sync.
"""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words
from textkit.counts import word_count

# Non-ASCII inputs are written as escapes so that NFC and NFD forms are unambiguous.
WORDS_CASES = [
    ("", []),
    ("hello", ["hello"]),
    ("Hello, world!", ["Hello", "world"]),
    ("!!! ... ?", []),
    ("  one \n\n two\t three  ", ["one", "two", "three"]),
    ("well-known", ["well-known"]),
    ("state-of-the-art design", ["state-of-the-art", "design"]),
    ("a -- b", ["a", "b"]),
    ("a--b", ["a", "b"]),
    ("-leading trailing-", ["leading", "trailing"]),
    ("don't", ["don't"]),
    ("it’s", ["it’s"]),
    ("'quoted'", ["quoted"]),
    ("the dogs' bones", ["the", "dogs", "bones"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000", ["1,000,000"]),
    ("-5", ["5"]),
    ("COVID-19", ["COVID-19"]),
    ("end.Start", ["end", "Start"]),
    ("e.g.", ["e", "g"]),
    ("1/2", ["1", "2"]),
    ("snake_case", ["snake", "case"]),
    ("naïve café", ["naïve", "café"]),
    ("naïve", ["naïve"]),
    ("日本語", ["日本語"]),
]

# Found by title, not number, like tests/test_counts.py does.
_DECISIONS = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions"
_ROW = re.compile(r"^\| `(.+)` \| (\d+) \|", re.M)


def _adr_cases() -> list[tuple[str, int]]:
    """Return the (input, count) rows of the word ADR's case table."""
    (adr,) = _DECISIONS.glob("[0-9][0-9][0-9][0-9]-what-counts-as-a-word.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    return [(ast.literal_eval(text), int(count)) for text, count in _ROW.findall(table)]


class WordsTest(unittest.TestCase):
    def test_adr_table(self):
        # One assertion per row of the ADR table, on the exact words, not only their count.
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(
            _adr_cases(), [(text, len(expected)) for text, expected in WORDS_CASES]
        )

    def test_joiner_at_the_very_end(self):
        # The lookahead must not run past the end of the text.
        self.assertEqual(words("well-"), ["well"])
        self.assertEqual(words("3."), ["3"])

    def test_word_count_is_the_number_of_words(self):
        text = "It's a well-known fact: 3.14 isn't exactly π -- or is it?"
        self.assertEqual(word_count(text), len(words(text)))
        self.assertEqual(len(words(text)), 11)

    def test_rejects_non_str(self):
        for value in (b"two words", ["two", "words"], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    words(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
