"""Tests for textkit.names (plan task T3.8, docs/phases/phase-3-converters.md)."""

import unicodedata
import unittest

from textkit.names import initials


class InitialsTest(unittest.TestCase):
    def test_plan_examples(self):
        # Every example listed in the plan task.
        cases = {
            "jean-luc picard": "JLP",
            "": "",
            "  jean--luc  picard ": "JLP",
            "o'brien": "O",
            "élodie durand": "ÉD",
            "3d printer": "DP",
            "- -": "",
            "ßa": "SS",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(initials(name), expected)

    def test_nfc_and_nfd_forms(self):
        # No Unicode normalization: the composed letter is kept, the decomposed form starts
        # with its bare base letter, whose combining accent is not a letter.
        nfc = unicodedata.normalize("NFC", "élodie")
        nfd = unicodedata.normalize("NFD", "élodie")
        self.assertNotEqual(nfc, nfd)
        self.assertEqual(initials(nfc), "É")
        self.assertEqual(initials(nfd), "E")

    def test_tab_is_not_a_separator(self):
        self.assertEqual(initials("jean\tluc"), "J")

    def test_cli_argument(self):
        # The phase-3 CLI rule: any str argument returns or raises only ValueError, KeyError
        # or TypeError; "a" returns.
        self.assertEqual(initials("a"), "A")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            initials(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
