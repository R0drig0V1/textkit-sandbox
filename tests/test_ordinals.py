"""Tests for textkit.ordinals, one TestCase class per public function.

OrdinalTest pins every example of plan task T3.9 (docs/phases/phase-3-converters.md) and the
phase-3 rules: a negative ``n`` or a non-``int`` (a ``bool`` included) raises ``ValueError``,
and the generic CLI arguments ``"a"`` and ``1`` raise nothing but ``ValueError``.
"""

import unittest

from textkit.ordinals import ordinal

# (n, expected) from T3.9.
CASES = [
    (0, "0th"),
    (1, "1st"),
    (2, "2nd"),
    (3, "3rd"),
    (4, "4th"),
    (11, "11th"),
    (12, "12th"),
    (13, "13th"),
    (21, "21st"),
    (22, "22nd"),
    (23, "23rd"),
    (101, "101st"),
    (111, "111th"),
    (112, "112th"),
    (113, "113th"),
    (1011, "1011th"),
    (1021, "1021st"),
]


class OrdinalTest(unittest.TestCase):
    def test_cases(self) -> None:
        for n, expected in CASES:
            with self.subTest(n=n):
                self.assertEqual(ordinal(n), expected)

    def test_negative_raises(self) -> None:
        for n in (-1, -11, -100):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    ordinal(n)

    def test_non_int_raises_value_error(self) -> None:
        # bool is an int subclass but is rejected; "a" is the CLI's generic text argument.
        for value in (True, False, 1.0, 1.5, "1", "a", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)  # type: ignore[arg-type]

    def test_cli_generic_int_argument(self) -> None:
        # T2.6 calls every one-parameter function with 1 for an int parameter.
        self.assertEqual(ordinal(1), "1st")


if __name__ == "__main__":
    unittest.main()
