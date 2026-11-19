"""Tests for textkit.ordinals: one TestCase class per public function."""

import unittest

from textkit.ordinals import ordinal


class OrdinalTest(unittest.TestCase):
    def test_spec_examples(self):
        cases = [
            (0, "0th"),
            (1, "1st"),
            (2, "2nd"),
            (11, "11th"),
            (101, "101st"),
            (111, "111th"),
            (112, "112th"),
            (113, "113th"),
            (1011, "1011th"),
            (1021, "1021st"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(ordinal(n), expected)

    def test_last_digit_rule(self):
        cases = [
            (3, "3rd"),
            (4, "4th"),
            (9, "9th"),
            (10, "10th"),
            (21, "21st"),
            (22, "22nd"),
            (23, "23rd"),
            (24, "24th"),
            (100, "100th"),
            (102, "102nd"),
            (103, "103rd"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(ordinal(n), expected)

    def test_teens_take_th(self):
        for n in (11, 12, 13, 211, 212, 213, 1012, 1013, 10**20 + 11):
            with self.subTest(n=n):
                self.assertTrue(ordinal(n).endswith("th"))

    def test_large_number(self):
        self.assertEqual(ordinal(10**20 + 1), f"{10**20 + 1}st")

    def test_rejects_negative(self):
        for n in (-1, -11, -21):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    ordinal(n)

    def test_rejects_non_int(self):
        for value in (True, False, 1.0, 1.5, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
