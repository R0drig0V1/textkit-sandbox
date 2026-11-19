"""Tests for textkit.numwords: the examples of plan task T3.4, the boundaries of every
word table, and the failure modes (out of range, non-int, bool)."""

import unittest

from textkit.numwords import number_to_words

# (input, expected output): the plan's examples first, then the table boundaries.
CASES = [
    (0, "zero"),
    (13, "thirteen"),
    (20, "twenty"),
    (42, "forty-two"),
    (100, "one hundred"),
    (105, "one hundred five"),
    (110, "one hundred ten"),
    (999, "nine hundred ninety-nine"),
    (1, "one"),
    (10, "ten"),
    (11, "eleven"),
    (19, "nineteen"),
    (21, "twenty-one"),
    (40, "forty"),
    (99, "ninety-nine"),
    (101, "one hundred one"),
    (119, "one hundred nineteen"),
    (120, "one hundred twenty"),
    (250, "two hundred fifty"),
    (311, "three hundred eleven"),
    (900, "nine hundred"),
]


class NumberToWordsTest(unittest.TestCase):
    def test_cases(self) -> None:
        for n, expected in CASES:
            with self.subTest(n=n):
                self.assertEqual(number_to_words(n), expected)

    def test_every_value_in_range_is_lower_case_without_and(self) -> None:
        for n in range(1000):
            with self.subTest(n=n):
                words = number_to_words(n)
                self.assertEqual(words, words.lower())
                self.assertNotIn("and", words.split())
                self.assertNotIn("  ", words)

    def test_out_of_range_raises(self) -> None:
        for n in (-1, 1000, 10**20, -(10**20)):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    number_to_words(n)

    def test_non_int_raises(self) -> None:
        for value in ("a", "1", 1.0, 1.5, None, [1]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    number_to_words(value)  # type: ignore[arg-type]

    def test_bool_raises(self) -> None:
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    number_to_words(value)

    def test_one_argument_from_cli_rules(self) -> None:
        # Phase 3 rule: called with 1 (an int parameter) it returns a string.
        self.assertEqual(number_to_words(1), "one")


if __name__ == "__main__":
    unittest.main()
