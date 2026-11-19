"""Tests for textkit.durations: the cases listed in plan task T3.11 of
docs/phases/phase-3-converters.md."""

import unittest

from textkit.durations import parse_duration


class ParseDurationTest(unittest.TestCase):
    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_hours_and_seconds(self):
        self.assertEqual(parse_duration("2h5s"), 7205)

    def test_all_three_parts(self):
        self.assertEqual(parse_duration("1h1m1s"), 3661)

    def test_values_are_not_range_limited(self):
        self.assertEqual(parse_duration("90m"), 5400)

    def test_zero_is_allowed(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_leading_zeros_are_allowed(self):
        self.assertEqual(parse_duration("01h"), 3600)

    def test_cli_argument_raises_value_error(self):
        # The phase-3 CLI rule: a one-parameter function is called with "a".
        with self.assertRaises(ValueError):
            parse_duration("a")

    def test_invalid_text_raises_value_error(self):
        cases = [
            "",  # no part at all
            "1H",  # upper-case unit
            "1h 30m",  # space between parts
            " 45s",  # leading space
            "30m1h",  # parts out of order
            "1h1h",  # repeated part
            "1.5h",  # decimal value
            "-1h",  # sign
            "45",  # no unit
            "45s\n",  # trailing newline (fullmatch, not match with "$")
            "١h",  # ARABIC-INDIC DIGIT ONE: ASCII digits only
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)


if __name__ == "__main__":
    unittest.main()
