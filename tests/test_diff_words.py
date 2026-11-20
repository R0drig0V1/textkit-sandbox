"""Tests for textkit/diff/words.py: ``diff_words`` over the words of ADR 0002 (plan task T3.6).

The words come from ``textkit._tokens.words`` (T3.3's ``Token``); ``diff_words`` compares
them by ``token.text`` only, so the same word at different offsets is equal.
"""

import random
import unittest

from textkit import _tokens
from textkit.diff import words


class DiffWordsTest(unittest.TestCase):
    def test_one_word_replaced(self):
        self.assertEqual(
            words.diff_words("the cat sat", "the dog sat"),
            [("=", "the"), ("-", "cat"), ("+", "dog"), ("=", "sat")],
        )

    def test_whitespace_and_punctuation_are_not_compared(self):
        self.assertEqual(
            words.diff_words("Hello,  world!", "Hello world\n"),
            [("=", "Hello"), ("=", "world")],
        )

    def test_words_follow_the_word_rule(self):
        # "well-known" and "don't" are one word each, "3.14" one number (ADR 0002).
        self.assertEqual(
            words.diff_words("a well-known fact, don't 3.14", "a well known fact, do not 3.14"),
            [
                ("=", "a"),
                ("-", "well-known"),
                ("+", "well"),
                ("+", "known"),
                ("=", "fact"),
                ("-", "don't"),
                ("+", "do"),
                ("+", "not"),
                ("=", "3.14"),
            ],
        )

    def test_comparison_is_exact(self):
        # No case folding and no normalization: "Cat" is not "cat", NFD is not NFC.
        self.assertEqual(words.diff_words("Cat", "cat"), [("-", "Cat"), ("+", "cat")])
        self.assertEqual(
            words.diff_words("café", "café"), [("-", "café"), ("+", "café")]
        )

    def test_same_word_at_other_offsets_is_equal(self):
        # The tokens differ (their offsets do), the words do not.
        self.assertEqual(
            words.diff_words("cat", "    cat"), [("=", "cat")]
        )
        self.assertNotEqual(_tokens.words("cat"), _tokens.words("    cat"))

    def test_texts_without_words(self):
        self.assertEqual(words.diff_words("", ""), [])
        self.assertEqual(words.diff_words("...", " - "), [])
        self.assertEqual(words.diff_words("", "a b"), [("+", "a"), ("+", "b")])
        self.assertEqual(words.diff_words("a b", "!"), [("-", "a"), ("-", "b")])

    def test_pairs_give_back_the_words_of_both_texts(self):
        rng = random.Random(7)
        vocabulary = ["the", "cat", "dog", "The", "naïve", "R2-D2", ",", "  ", "\n"]
        for _ in range(100):
            a = " ".join(rng.choice(vocabulary) for _ in range(rng.randint(0, 8)))
            b = " ".join(rng.choice(vocabulary) for _ in range(rng.randint(0, 8)))
            pairs = words.diff_words(a, b)
            with self.subTest(a=a, b=b):
                self.assertEqual([w for op, w in pairs if op != "+"], [t.text for t in _tokens.words(a)])
                self.assertEqual([w for op, w in pairs if op != "-"], [t.text for t in _tokens.words(b)])
                self.assertTrue(all(op in ("=", "-", "+") for op, _ in pairs))

    def test_tie_rule_deletes_first(self):
        self.assertEqual(
            words.diff_words("a b", "b a"), [("-", "a"), ("=", "b"), ("+", "a")]
        )

    def test_returns_lists_of_str_tuples(self):
        pairs = words.diff_words("x y", "x z")
        self.assertIsInstance(pairs, list)
        for pair in pairs:
            self.assertIsInstance(pair, tuple)
            self.assertEqual([type(item) for item in pair], [str, str])

    def test_wrong_types_raise_type_error(self):
        for args in ((b"a", "b"), ("a", None)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    words.diff_words(*args)


if __name__ == "__main__":
    unittest.main()
