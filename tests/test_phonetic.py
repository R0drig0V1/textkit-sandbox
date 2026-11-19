"""Tests for textkit.phonetic (plan task T3.7, docs/phases/phase-3-converters.md)."""

import unicodedata
import unittest

from textkit.phonetic import soundex


class SoundexTest(unittest.TestCase):
    def test_plan_examples(self):
        # Every code listed in the plan task; Ashcraft, Pfister and Tymczak tell the Soundex
        # variants apart (H/W transparent, first letter de-duplicated, vowel separates).
        cases = {
            "Robert": "R163",
            "Rupert": "R163",
            "Tymczak": "T522",
            "Ashcraft": "A261",
            "Pfister": "P236",
            "Honeyman": "H555",
            "Lee": "L000",
            "O'Brien": "O165",
            "José": "J200",
        }
        for name, code in cases.items():
            with self.subTest(name=name):
                self.assertEqual(soundex(name), code)

    def test_no_ascii_letter_raises_value_error(self):
        for name in ("", "123", "é"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    soundex(name)

    def test_single_letter_cli_argument(self):
        # The generic CLI run (T2.6) calls every one-parameter function with "a".
        self.assertEqual(soundex("a"), "A000")

    def test_case_is_ignored(self):
        self.assertEqual(soundex("rObErT"), "R163")
        self.assertEqual(soundex("ROBERT"), "R163")

    def test_non_letters_are_transparent_not_separators(self):
        # Removed before coding: the two 2-coded letters stay adjacent and are coded once.
        self.assertEqual(soundex("Ash-craft"), soundex("Ashcraft"))
        self.assertEqual(soundex("Tym cz4ak"), "T522")
        self.assertEqual(soundex("  ' 1lee"), "L000")

    def test_h_and_w_are_transparent(self):
        # S and C (both 2) separated only by H: coded once. Separated by a vowel: twice.
        self.assertEqual(soundex("Bshc"), "B200")
        self.assertEqual(soundex("Bswc"), "B200")
        self.assertEqual(soundex("Bsac"), "B220")

    def test_first_letter_takes_part_in_deduplication(self):
        self.assertEqual(soundex("Pf"), "P000")
        self.assertEqual(soundex("Phf"), "P000")
        self.assertEqual(soundex("Paf"), "P100")

    def test_cut_to_four_characters(self):
        self.assertEqual(soundex("Bcdlmr"), "B234")

    def test_nfd_input_gives_the_same_code(self):
        self.assertEqual(soundex(unicodedata.normalize("NFD", "José")), "J200")

    def test_non_ascii_letters_that_map_to_ascii_are_removed(self):
        # "ß".upper() is "SS" and the Kelvin sign lower-cases to "k": neither is ASCII.
        for name in ("ß", "K", "ſ"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    soundex(name)
        self.assertEqual(soundex("ßLee"), "L000")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            soundex(1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
