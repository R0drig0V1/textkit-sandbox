"""Tests for textkit.durations, one TestCase class per public function.

ParseDurationTest covers every example and every rejected input listed in plan task T3.11
(docs/phases/phase-3-converters.md), plus the phase-3 CLI rule: a call with ``"a"`` raises
only ``ValueError``, ``KeyError`` or ``TypeError``.
"""

import unittest

from textkit.durations import parse_duration


class ParseDurationTest(unittest.TestCase):
    """``parse_duration``: h, m and s parts in that order, at least one, ASCII digits."""

    def test_valid_durations(self) -> None:
        cases = [
            ("1h30m", 5400),
            ("45s", 45),
            ("2h5s", 7205),
            ("90m", 5400),
            ("0s", 0),
            ("01h", 3600),
            ("1h1m1s", 3661),
            ("5m", 300),
            ("0h0m0s", 0),
            ("100000h", 360000000),
        ]
        for text, seconds in cases:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), seconds)

    def test_returns_int(self) -> None:
        self.assertIs(type(parse_duration("1h")), int)

    def test_invalid_durations_raise_value_error(self) -> None:
        for text in ["", "1H", "1h 30m", " 45s", "30m1h", "1h1h", "1.5h", "-1h", "45",
                     "45s\n", "١h", "a", "h", "1h30", "+1h"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_str_raises_type_error(self) -> None:
        for value in [None, 45, b"45s"]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
