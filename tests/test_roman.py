"""Tests for textkit.roman, one TestCase class per public function.

ToRomanTest pins the T3.3 contract (docs/phases/phase-3-converters.md): standard subtractive
form for 1..3999, ``ValueError`` for anything else, a ``bool`` and the CLI's ``"a"`` and
``1`` included (phase-3 rule "No CLI edits").
"""

import unittest

from textkit.roman import to_roman


class ToRomanTest(unittest.TestCase):
    def test_plan_example(self) -> None:
        self.assertEqual(to_roman(1994), "MCMXCIV")

    def test_known_values(self) -> None:
        cases = [
            (1, "I"),
            (2, "II"),
            (3, "III"),
            (4, "IV"),
            (5, "V"),
            (6, "VI"),
            (9, "IX"),
            (10, "X"),
            (14, "XIV"),
            (40, "XL"),
            (44, "XLIV"),
            (49, "XLIX"),
            (50, "L"),
            (90, "XC"),
            (99, "XCIX"),
            (100, "C"),
            (400, "CD"),
            (444, "CDXLIV"),
            (500, "D"),
            (900, "CM"),
            (999, "CMXCIX"),
            (1000, "M"),
            (2024, "MMXXIV"),
            (3888, "MMMDCCCLXXXVIII"),
            (3999, "MMMCMXCIX"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_range_bounds(self) -> None:
        self.assertEqual(to_roman(1), "I")
        self.assertEqual(to_roman(3999), "MMMCMXCIX")
        for n in (0, -1, 4000, 10**6):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_standard_form_for_every_value(self) -> None:
        # Standard form: only these symbols, none repeated four times in a row.
        for n in range(1, 4000):
            numeral = to_roman(n)
            with self.subTest(n=n):
                self.assertTrue(set(numeral) <= set("IVXLCDM"))
                for symbol in "IXCM":
                    self.assertNotIn(symbol * 4, numeral)
                for symbol in "VLD":
                    self.assertLessEqual(numeral.count(symbol), 1)

    def test_values_are_distinct(self) -> None:
        self.assertEqual(len({to_roman(n) for n in range(1, 4000)}), 3999)

    def test_non_int_raises_value_error(self) -> None:
        for value in (True, False, 1.0, 1.5, "1", "a", None, [1]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    to_roman(value)  # type: ignore[arg-type]

    def test_cli_arguments_raise_only_value_error_or_succeed(self) -> None:
        # T2.6 calls the function with "a" and with 1; only ValueError, KeyError or
        # TypeError may escape, and 1 is valid here.
        with self.assertRaises(ValueError):
            to_roman("a")  # type: ignore[arg-type]
        self.assertEqual(to_roman(1), "I")


if __name__ == "__main__":
    unittest.main()
