"""Tests for textkit.roman: one TestCase class per public function."""

import unittest

from textkit.roman import to_roman


class ToRomanTest(unittest.TestCase):
    def test_spec_example(self):
        self.assertEqual(to_roman(1994), "MCMXCIV")

    def test_known_values(self):
        cases = [
            (1, "I"),
            (2, "II"),
            (3, "III"),
            (4, "IV"),
            (5, "V"),
            (9, "IX"),
            (10, "X"),
            (14, "XIV"),
            (40, "XL"),
            (49, "XLIX"),
            (90, "XC"),
            (400, "CD"),
            (444, "CDXLIV"),
            (900, "CM"),
            (1000, "M"),
            (2024, "MMXXIV"),
            (3888, "MMMDCCCLXXXVIII"),
            (3999, "MMMCMXCIX"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_round_trip_whole_range(self):
        # An independent decoder: every value in range maps to a distinct numeral that
        # decodes back to it, so the greedy table has no gaps or overlaps.
        values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

        def decode(numeral):
            total = 0
            for i, ch in enumerate(numeral):
                v = values[ch]
                if i + 1 < len(numeral) and values[numeral[i + 1]] > v:
                    total -= v
                else:
                    total += v
            return total

        seen = set()
        for n in range(1, 4000):
            numeral = to_roman(n)
            self.assertEqual(decode(numeral), n)
            self.assertNotIn(numeral, seen)
            seen.add(numeral)
            # Standard form: no symbol four times in a row.
            for ch in "IXCM":
                self.assertNotIn(ch * 4, numeral)

    def test_out_of_range_raises(self):
        for n in (0, -1, 4000, 10**6):
            with self.subTest(n=n), self.assertRaises(ValueError):
                to_roman(n)

    def test_non_int_raises(self):
        for n in (True, False, 4.0, 1.5, "a", "4", None, [4]):
            with self.subTest(n=n), self.assertRaises(ValueError):
                to_roman(n)

    def test_cli_probe_values(self):
        # Phase 3 rule: the T2.6 CLI probes with "a" and 1.
        with self.assertRaises(ValueError):
            to_roman("a")
        self.assertEqual(to_roman(1), "I")


if __name__ == "__main__":
    unittest.main()
