"""Tests for textkit/diff/words.py: ``diff_words`` (plan task T3.6).

Words come from ``textkit._tokens.words`` (ADR 0002) and are compared by ``token.text``
only (plan task T3.3); the pairs follow the tie rule of ``lcs.edit_script``.
"""

import random
import unittest

import textkit.diff
from textkit._tokens import words
from textkit.diff.words import diff_words


class DiffWordsTest(unittest.TestCase):
    def test_kept_deleted_and_inserted_words(self):
        self.assertEqual(
            diff_words("The quick brown fox", "the quick red fox, jumps"),
            [("-", "The"), ("+", "the"), ("=", "quick"), ("-", "brown"), ("+", "red"),
             ("=", "fox"), ("+", "jumps")],
        )

    def test_empty_and_equal_texts(self):
        self.assertEqual(diff_words("", ""), [])
        self.assertEqual(diff_words("!!", " ... "), [])  # no words on either side
        self.assertEqual(diff_words("a b", "a b"), [("=", "a"), ("=", "b")])

    def test_whitespace_and_punctuation_are_not_compared(self):
        # The words are equal, so the texts are equal for diff_words.
        self.assertEqual(
            diff_words("well-known,  don't\n3.14", "well-known don't... 3.14!"),
            [("=", "well-known"), ("=", "don't"), ("=", "3.14")],
        )

    def test_words_are_exactly_as_in_their_text(self):
        # NFD "café" is not NFC "café": no normalization, and the mark stays in its word.
        self.assertEqual(
            diff_words("café x", "café x"),
            [("-", "café"), ("+", "café"), ("=", "x")],
        )

    def test_pairs_rebuild_both_word_lists(self):
        rng = random.Random(36)
        vocabulary = ["a", "b", "c", "don't", "3.14"]
        for _ in range(200):
            a = " ".join(rng.choice(vocabulary) for _ in range(rng.randint(0, 8)))
            b = ", ".join(rng.choice(vocabulary) for _ in range(rng.randint(0, 8)))
            pairs = diff_words(a, b)
            with self.subTest(a=a, b=b):
                self.assertEqual([w for op, w in pairs if op != "+"],
                                 [t.text for t in words(a)])
                self.assertEqual([w for op, w in pairs if op != "-"],
                                 [t.text for t in words(b)])
                for run in "".join(op for op, _ in pairs).split("="):
                    self.assertNotIn("+-", run)

    def test_exported_from_the_package(self):
        self.assertIs(textkit.diff.diff_words, diff_words)
        self.assertEqual(textkit.diff.__all__, ["apply_patch", "diff_words", "unified_diff"])

    def test_wrong_types_are_rejected(self):
        for args in ((b"a", "b"), ("a", None)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    diff_words(*args)


if __name__ == "__main__":
    unittest.main()
