"""Tests for textkit.ciphers."""
import string
import unittest

from textkit.ciphers import rot13


class Rot13Test(unittest.TestCase):
    def test_examples(self):
        cases = {
            "": "",
            "a": "n",
            "n": "a",
            "z": "m",
            "A": "N",
            "Z": "M",
            "Hello, World!": "Uryyb, Jbeyq!",
            "abcdefghijklmnopqrstuvwxyz": "nopqrstuvwxyzabcdefghijklm",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ": "NOPQRSTUVWXYZABCDEFGHIJKLM",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(rot13(text), expected)

    def test_non_letters_unchanged(self):
        others = string.digits + string.punctuation + " \t\n"
        self.assertEqual(rot13(others), others)

    def test_non_ascii_letters_unchanged(self):
        self.assertEqual(rot13("é ñ ß Ω ü"), "é ñ ß Ω ü")
        self.assertEqual(rot13("José"), "Wbfé")

    def test_is_its_own_inverse(self):
        samples = ["", "a", "Hello, World!", "José 123", string.printable, "ÀbÇ-xyz_Ω"]
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(rot13(rot13(text)), text)

    def test_non_str_raises_type_error(self):
        for value in (None, 1, b"abc"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    rot13(value)


if __name__ == "__main__":
    unittest.main()
