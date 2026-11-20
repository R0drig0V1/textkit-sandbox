"""Tests for textkit._tokens (the private shared tokenizer). One TestCase class per function."""

import ast
import pathlib
import re
import unittest

from textkit._tokens import Token, words

# The case table of the word-rule ADR (docs/decisions/*-word-count-what-counts-as-a-word.md),
# row by row and in the same order, with the words (token texts) each input must produce. The
# ADR table gives only counts; WordsTest checks that these rows are exactly the ADR's inputs
# and that each list has the ADR's count, so the token lists cannot drift from the table.
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


def _texts(tokens: list) -> list:
    """Return the text of each token, for comparing words without their offsets."""
    return [token.text for token in tokens]


class WordsTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORDS_CASES:
            with self.subTest(text=text):
                self.assertEqual(_texts(words(text)), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(
            [(text, len(expected)) for text, expected in WORDS_CASES], _adr_cases()
        )

    def test_returns_tokens(self):
        (token,) = words("hello")
        self.assertIsInstance(token, Token)
        self.assertEqual(token, Token("hello", 0, 5))
        self.assertEqual((token.text, token.start, token.end), ("hello", 0, 5))

    def test_returns_words_unchanged_in_order(self):
        # No case folding or normalization: the words are slices of the input.
        self.assertEqual(
            words("Zeta, ALPHA beta"),
            [Token("Zeta", 0, 4), Token("ALPHA", 6, 11), Token("beta", 12, 16)],
        )

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    words(bad)

    # The offsets of ADR 0002, section "Offsets".

    def test_offsets_slice_the_input_on_every_adr_row(self):
        # The rows come from the ADR itself, so a new row is covered without editing this test.
        for text, _count in _adr_cases():
            for token in words(text):
                with self.subTest(text=text, token=token):
                    self.assertEqual(text[token.start : token.end], token.text)

    def test_offsets_increase_and_do_not_overlap(self):
        texts = [text for text, _count in _adr_cases()]
        texts += ["the cat the cat", "a a a a", "x-y, 3.14; don't  stop\n\tnow"]
        for text in texts:
            tokens = words(text)
            with self.subTest(text=text):
                for token in tokens:
                    self.assertLess(token.start, token.end)
                for before, after in zip(tokens, tokens[1:]):
                    self.assertLess(before.start, after.start)
                    self.assertLessEqual(before.end, after.start)

    def test_repeated_word_has_its_own_offsets(self):
        # A search for the word's text would give the first "the" (0, 3) both times.
        self.assertEqual(
            words("the cat the cat"),
            [
                Token("the", 0, 3),
                Token("cat", 4, 7),
                Token("the", 8, 11),
                Token("cat", 12, 15),
            ],
        )

    def test_offsets_count_code_points_outside_the_bmp(self):
        # U+1F600 is one code point (two UTF-16 units, four UTF-8 bytes) and not a word.
        self.assertEqual(words("\U0001F600 ab"), [Token("ab", 2, 4)])

    def test_combining_marks_stay_inside_their_word(self):
        # NFD: "e" followed by U+0301 COMBINING ACUTE ACCENT; the text is not normalized.
        self.assertEqual(
            words("cafe\u0301 x"), [Token("cafe\u0301", 0, 5), Token("x", 6, 7)]
        )

    def test_no_words_gives_no_tokens(self):
        for text in ("", "   ", "!!! ... ---", "\u0301"):
            with self.subTest(text=text):
                self.assertEqual(words(text), [])


if __name__ == "__main__":
    unittest.main()
