"""Tests for textkit.ciphers (plan task T3.2, docs/phases/phase-3-converters.md)."""

import string
import unittest

from textkit.ciphers import rot13


class Rot13Test(unittest.TestCase):
    def test_rotates_ascii_letters_keeping_case(self):
        cases = {
            "abcdefghijklmnopqrstuvwxyz": "nopqrstuvwxyzabcdefghijklm",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ": "NOPQRSTUVWXYZABCDEFGHIJKLM",
            "Hello, World!": "Uryyb, Jbeyq!",
            "Why did the chicken cross the road?": "Jul qvq gur puvpxra pebff gur ebnq?",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(rot13(text), expected)

    def test_single_letter_cli_argument(self):
        # The generic CLI run (T2.6) calls every one-parameter function with "a".
        self.assertEqual(rot13("a"), "n")

    def test_empty_string(self):
        self.assertEqual(rot13(""), "")

    def test_other_characters_are_unchanged(self):
        # Digits, punctuation, whitespace and non-ASCII letters (including ones whose case
        # mapping lands on ASCII, such as "ß" and the Kelvin sign) do not move.
        for text in ("0123456789", string.punctuation, " \t\n", "éñüß", "K", "日本語"):
            with self.subTest(text=text):
                self.assertEqual(rot13(text), text)

    def test_mixed_text(self):
        self.assertEqual(rot13("Ñandú 42 años"), "Ñnaqú 42 nñbf")

    def test_is_its_own_inverse(self):
        samples = ("", "a", "Hello, World!", string.printable, "Ñandú 42 años", "K z")
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(rot13(rot13(text)), text)

    def test_non_str_raises_type_error(self):
        for value in (None, 1, b"abc"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    rot13(value)  # type: ignore[arg-type]
