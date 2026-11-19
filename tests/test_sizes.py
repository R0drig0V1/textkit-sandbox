"""Tests for textkit.sizes: one TestCase class per public function."""

import unittest

from textkit.sizes import human_bytes


class HumanBytesTest(unittest.TestCase):
    def test_spec_cases(self):
        cases = [
            (0, "0 B"),
            (1, "1 B"),
            (1023, "1023 B"),
            (1024, "1.0 KiB"),
            (1280, "1.2 KiB"),
            (1536, "1.5 KiB"),
            (1048575, "1024.0 KiB"),
            (1048576, "1.0 MiB"),
            (1024**4, "1.0 TiB"),
            (1024**5, "1024.0 TiB"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(human_bytes(n), expected)

    def test_every_unit_boundary(self):
        # Each unit starts exactly at 1024**k; the byte before it stays in the unit below,
        # where the quotient rounds up to 1024.0 (the unit is chosen before rounding).
        below = {1: "1023 B", 2: "1024.0 KiB", 3: "1024.0 MiB", 4: "1024.0 GiB"}
        for k, unit in enumerate(("KiB", "MiB", "GiB", "TiB"), start=1):
            with self.subTest(unit=unit):
                self.assertEqual(human_bytes(1024**k), f"1.0 {unit}")
                self.assertEqual(human_bytes(1024**k - 1), below[k])

    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            human_bytes(-1)

    def test_rejects_non_int(self):
        for value in (1.5, 1024.0, True, False, "a", "1024", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    human_bytes(value)

    def test_overflow_is_value_error(self):
        with self.assertRaises(ValueError):
            human_bytes(10**400)


if __name__ == "__main__":
    unittest.main()
