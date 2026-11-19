"""Tests for textkit.distance (plan task T3.1, docs/phases/phase-3-converters.md)."""

import itertools
import unicodedata
import unittest

from textkit.distance import levenshtein


def _brute_force(a: str, b: str) -> int:
    """Reference distance from the plain recursive definition (only for short strings)."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    return min(
        _brute_force(a[1:], b) + 1,
        _brute_force(a, b[1:]) + 1,
        _brute_force(a[1:], b[1:]) + (a[0] != b[0]),
    )


class LevenshteinTest(unittest.TestCase):
    def test_plan_examples(self):
        self.assertEqual(levenshtein("", ""), 0)
        self.assertEqual(levenshtein("kitten", "sitting"), 3)

    def test_empty_side_gives_the_other_length(self):
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("abc", ""), 3)

    def test_single_character_argument(self):
        # The value the generic CLI run (T2.6) uses for one-parameter functions.
        self.assertEqual(levenshtein("a", "a"), 0)
        self.assertEqual(levenshtein("a", ""), 1)
        self.assertEqual(levenshtein("a", "b"), 1)

    def test_known_distances(self):
        cases = {
            ("flaw", "lawn"): 2,
            ("saturday", "sunday"): 3,
            ("gumbo", "gambol"): 2,
            ("book", "back"): 2,
            ("abc", "abc"): 0,
            ("abc", "xyz"): 3,
            ("ab", "ba"): 2,  # a transposition is two edits, not one
        }
        for (a, b), distance in cases.items():
            with self.subTest(a=a, b=b):
                self.assertEqual(levenshtein(a, b), distance)
                self.assertEqual(levenshtein(b, a), distance)

    def test_case_matters(self):
        self.assertEqual(levenshtein("Kitten", "kitten"), 1)

    def test_no_unicode_normalization(self):
        nfc = unicodedata.normalize("NFC", "é")
        nfd = unicodedata.normalize("NFD", "é")
        self.assertEqual(levenshtein(nfc, nfc), 0)
        self.assertEqual(levenshtein(nfc, nfd), 2)
        self.assertEqual(levenshtein("café", "cafe"), 1)

    def test_matches_brute_force_on_all_short_strings(self):
        words = ["".join(p) for n in range(4) for p in itertools.product("ab", repeat=n)]
        for a, b in itertools.product(words, repeat=2):
            with self.subTest(a=a, b=b):
                self.assertEqual(levenshtein(a, b), _brute_force(a, b))

    def test_long_strings(self):
        self.assertEqual(levenshtein("a" * 500, "a" * 500), 0)
        self.assertEqual(levenshtein("a" * 500, "b" * 300), 500)

    def test_non_str_raises_type_error(self):
        for a, b in ((1, "a"), ("a", 1), (None, None), (["a"], "a"), (b"a", "a")):
            with self.subTest(a=a, b=b):
                with self.assertRaises(TypeError):
                    levenshtein(a, b)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
