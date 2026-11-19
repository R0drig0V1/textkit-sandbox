"""Tests for textkit.phonetic."""
import unittest

from textkit.phonetic import soundex


class SoundexTest(unittest.TestCase):
    def test_plan_examples(self):
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
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(soundex(name), expected)

    def test_no_ascii_letter_raises(self):
        for name in ("", "123", "é"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    soundex(name)

    def test_case_is_ignored(self):
        self.assertEqual(soundex("robert"), "R163")
        self.assertEqual(soundex("ROBERT"), soundex("robert"))

    def test_non_letters_are_transparent_not_separators(self):
        # "Ash-craft": the hyphen is removed, so H still joins S and C into one digit.
        self.assertEqual(soundex("Ash-craft"), "A261")
        self.assertEqual(soundex(" 1Lee! "), "L000")

    def test_h_and_w_collapse_but_vowels_separate(self):
        self.assertEqual(soundex("Ashcraft"), "A261")  # S H C: coded once
        self.assertEqual(soundex("Tymczak"), "T522")  # Z A K: coded twice

    def test_first_letter_digit_counts(self):
        self.assertEqual(soundex("Pfister"), "P236")  # F not coded after P
        self.assertEqual(soundex("Bb"), "B000")

    def test_cut_to_four_characters(self):
        self.assertEqual(soundex("Washington"), "W252")

    def test_single_letter(self):
        # Phase 3 rule: a one-parameter function accepts the CLI probe "a".
        self.assertEqual(soundex("a"), "A000")


if __name__ == "__main__":
    unittest.main()
