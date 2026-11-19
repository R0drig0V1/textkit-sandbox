"""Tests for textkit.sizes, one TestCase class per public function.

HumanBytesTest pins every example of plan task T3.10 (docs/phases/phase-3-converters.md),
the rejected inputs, and the phase-3 CLI rule: called with ``1`` it returns a ``str``, and
called with ``"a"`` it raises only ``ValueError``.
"""

import unittest

from textkit.sizes import human_bytes

# Every output pinned by T3.10: (n, expected).
CASES = [
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


class HumanBytesTest(unittest.TestCase):
    def test_cases(self) -> None:
        for n, expected in CASES:
            with self.subTest(n=n):
                self.assertEqual(human_bytes(n), expected)

    def test_gib(self) -> None:
        # Not in the plan's list, but the only unit it does not reach.
        self.assertEqual(human_bytes(3 * 1024**3), "3.0 GiB")

    def test_rejects_negative_and_non_int(self) -> None:
        for n in (-1, 1.5, True, False, "a", "1", None):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    human_bytes(n)  # type: ignore[arg-type]

    def test_overflow_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            human_bytes(10**400)

    def test_cli_arguments(self) -> None:
        # Phase-3 rule "No CLI edits": T2.6 passes 1 for an int parameter, and "a" must
        # raise one of the errors the CLI maps to exit 1.
        self.assertEqual(human_bytes(1), "1 B")
        with self.assertRaises(ValueError):
            human_bytes("a")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
