"""Tests for textkit.numwords, one TestCase class per public function.

NumberToWordsTest pins every example of plan task T3.4 (docs/phases/phase-3-converters.md),
the range edges, the rejection of non-``int`` and ``bool`` arguments with ``ValueError``,
and the phase-3 rule that the function called with ``"a"`` or ``1`` (what the CLI's generic
test passes) raises nothing but ``ValueError``.
"""

import unittest

from textkit.numwords import number_to_words


class NumberToWordsTest(unittest.TestCase):
    """number_to_words: the T3.4 examples, the range edges and the rejected arguments."""

    def test_plan_examples(self) -> None:
        cases = [
            (0, "zero"),
            (13, "thirteen"),
            (20, "twenty"),
            (42, "forty-two"),
            (100, "one hundred"),
            (105, "one hundred five"),
            (110, "one hundred ten"),
            (999, "nine hundred ninety-nine"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(number_to_words(n), expected)

    def test_other_values(self) -> None:
        cases = [
            (1, "one"),
            (10, "ten"),
            (11, "eleven"),
            (19, "nineteen"),
            (21, "twenty-one"),
            (40, "forty"),
            (90, "ninety"),
            (99, "ninety-nine"),
            (101, "one hundred one"),
            (115, "one hundred fifteen"),
            (120, "one hundred twenty"),
            (342, "three hundred forty-two"),
            (500, "five hundred"),
            (880, "eight hundred eighty"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(number_to_words(n), expected)

    def test_whole_range_is_lower_case_without_and(self) -> None:
        for n in range(1000):
            with self.subTest(n=n):
                words = number_to_words(n)
                self.assertEqual(words, words.lower())
                self.assertNotIn("and", words.split())
                self.assertNotIn("  ", words)
                self.assertEqual(words, words.strip())

    def test_out_of_range_raises(self) -> None:
        for n in (-1, -999, 1000, 10**20):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    number_to_words(n)

    def test_non_int_raises_value_error(self) -> None:
        for value in (True, False, 1.0, 1.5, "1", "a", None, [1]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    number_to_words(value)  # type: ignore[arg-type]

    def test_cli_arguments(self) -> None:
        # The generic CLI test (T2.6) calls every one-parameter function with "a" and, for
        # an int parameter, with 1: only ValueError, KeyError or TypeError may escape.
        with self.assertRaises(ValueError):
            number_to_words("a")  # type: ignore[arg-type]
        self.assertEqual(number_to_words(1), "one")


if __name__ == "__main__":
    unittest.main()
