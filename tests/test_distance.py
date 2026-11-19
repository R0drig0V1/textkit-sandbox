"""Tests for textkit.distance: one TestCase class per public function."""

import unittest

from textkit.distance import levenshtein


class LevenshteinTest(unittest.TestCase):
    def test_both_empty(self):
        self.assertEqual(levenshtein("", ""), 0)

    def test_kitten_sitting(self):
        self.assertEqual(levenshtein("kitten", "sitting"), 3)

    def test_identical(self):
        self.assertEqual(levenshtein("textkit", "textkit"), 0)

    def test_one_empty_is_length_of_other(self):
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("abc", ""), 3)

    def test_single_insertion_deletion_substitution(self):
        self.assertEqual(levenshtein("cat", "cart"), 1)
        self.assertEqual(levenshtein("cart", "cat"), 1)
        self.assertEqual(levenshtein("cat", "cut"), 1)

    def test_symmetric(self):
        for a, b in [("flaw", "lawn"), ("saturday", "sunday"), ("a", "bcd")]:
            self.assertEqual(levenshtein(a, b), levenshtein(b, a))

    def test_known_values(self):
        self.assertEqual(levenshtein("flaw", "lawn"), 2)
        self.assertEqual(levenshtein("saturday", "sunday"), 3)

    def test_transposition_costs_two(self):
        # No Damerau transpositions: swapping two characters is two substitutions.
        self.assertEqual(levenshtein("ab", "ba"), 2)

    def test_case_sensitive(self):
        self.assertEqual(levenshtein("A", "a"), 1)

    def test_code_points_without_normalization(self):
        nfc = "\u00e9"  # "é" as one code point
        nfd = "e\u0301"  # "é" as "e" plus a combining acute accent
        self.assertEqual(levenshtein(nfc, "e"), 1)
        self.assertEqual(levenshtein(nfd, "e"), 1)  # delete the accent
        self.assertEqual(levenshtein(nfc, nfd), 2)  # substitute, then insert the accent

    def test_single_character_argument(self):
        self.assertEqual(levenshtein("a", "a"), 0)
        self.assertEqual(levenshtein("a", ""), 1)

    def test_non_str_raises_type_error(self):
        for a, b in [(1, "a"), ("a", None), (["a"], ["a"]), (b"a", b"a")]:
            with self.assertRaises(TypeError):
                levenshtein(a, b)


if __name__ == "__main__":
    unittest.main()
