"""Tests for textkit._tokens, the shared tokenizer behind ADR 0001's word rule."""

import ast
import itertools
import pathlib
import re
import unittest

from textkit._tokens import words

REPO = pathlib.Path(__file__).resolve().parent.parent

# Every row of the case table in ADR 0001 (docs/decisions/0001-what-counts-as-a-word.md), in
# the same order, with the words each input splits into; the ADR's count is the length of the
# list. test_adr_table_matches keeps the inputs and counts in sync with the ADR. Non-ASCII
# literals are escaped so that the NFD row is visibly NFD.
WORDS_CASES = [
    ("", []),
    ("  \n\t  ", []),
    ("... !!! ?", []),
    ("hello", ["hello"]),
    ("Hello, world!", ["Hello", "world"]),
    ("one  two\n\nthree\tfour", ["one", "two", "three", "four"]),
    ("well-known", ["well-known"]),
    ("state-of-the-art", ["state-of-the-art"]),
    ("well - known", ["well", "known"]),
    ("-leading trailing-", ["leading", "trailing"]),
    ("a--b", ["a", "b"]),
    ("word—word", ["word", "word"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("rock'n'roll", ["rock'n'roll"]),
    ("'quoted'", ["quoted"]),
    ("dogs' bowls", ["dogs", "bowls"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000", ["1,000,000"]),
    ("1, 2, 3", ["1", "2", "3"]),
    ("v2.0", ["v2.0"]),
    ("end.Start", ["end", "Start"]),
    ("e.g.", ["e", "g"]),
    ("snake_case", ["snake", "case"]),
    ("naïve café", ["naïve", "café"]),
    ("Ñandú", ["Ñandú"]),
    ("日本語", ["日本語"]),
    ("C++ and C#", ["C", "and", "C"]),
    ("50%", ["50"]),
    ("-5", ["5"]),
]


def _adr_cases() -> list[tuple[str, int]]:
    """Read the (input, count) rows of ADR 0001's case table, whatever its number."""
    # Matched by title, not number, like tests/test_cases.py does for its ADR.
    (adr,) = (REPO / "docs" / "decisions").glob("*-what-counts-as-a-word.md")
    rows = re.findall(r'^\| `(".*?")` \| (\d+) \|', adr.read_text(), re.M)
    return [(ast.literal_eval(text), int(count)) for text, count in rows]


class WordsTest(unittest.TestCase):
    # One assertion per row of ADR 0001's table, as the T1.10 acceptance criteria require.
    def test_adr_0001_cases(self):
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_adr_table_matches(self):
        self.assertEqual(_adr_cases(), [(text, len(found)) for text, found in WORDS_CASES])

    def test_nfc_and_nfd_split_the_same(self):
        # Rule 2: a combining mark continues a word, so only the code points differ.
        self.assertEqual(len(words("Ñandú es")), len(words("Ñandú es")))
        self.assertEqual(words("Ñandú es"), ["Ñandú", "es"])

    def test_combining_mark_never_starts_a_word(self):
        self.assertEqual(words("́a ́"), ["a"])

    def test_words_are_unchanged_slices_in_order(self):
        text = "Don't stop, 3.14!"
        found = words(text)
        self.assertEqual(found, ["Don't", "stop", "3.14"])
        # Each word occurs in `text` after the end of the previous one.
        position = 0
        for word in found:
            position = text.find(word, position)
            self.assertGreaterEqual(position, 0, word)
            position += len(word)

    def test_number_separator_needs_digits_on_both_sides(self):
        self.assertEqual(words("1.a a.1 1."), ["1", "a", "a", "1", "1"])

    def test_underscore_names_split_like_snake_case_rule_1(self):
        # textkit.cases.to_snake_case relies on this: for names of ASCII letters, digits and
        # `_`, `words` gives the parts between runs of `_`, leading and trailing ones dropped.
        for length in range(6):
            for chars in itertools.product("aB1_", repeat=length):
                name = "".join(chars)
                with self.subTest(name=name):
                    expected = [part for part in re.split(r"_+", name) if part]
                    self.assertEqual(words(name), expected)

    def test_rejects_non_str(self):
        for value in (None, 42, b"text", ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    words(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
