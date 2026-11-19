"""Tests for textkit.names: the cases listed in plan task T3.8 of
docs/phases/phase-3-converters.md."""

import unicodedata
import unittest

from textkit.names import initials


class InitialsTest(unittest.TestCase):
    def test_spaces_and_hyphens_separate_parts(self):
        self.assertEqual(initials("jean-luc picard"), "JLP")

    def test_empty_string(self):
        self.assertEqual(initials(""), "")

    def test_single_letter(self):
        # The phase-3 CLI rule: a one-parameter function is called with "a".
        self.assertEqual(initials("a"), "A")

    def test_runs_and_surrounding_separators_are_ignored(self):
        self.assertEqual(initials("  jean--luc  picard "), "JLP")

    def test_apostrophe_does_not_separate(self):
        self.assertEqual(initials("o'brien"), "O")

    def test_composed_accented_letter(self):
        self.assertEqual(initials(unicodedata.normalize("NFC", "élodie durand")), "ÉD")

    def test_decomposed_accented_letter_gives_base_letter(self):
        self.assertEqual(initials(unicodedata.normalize("NFD", "élodie")), "E")

    def test_leading_non_letters_are_skipped(self):
        self.assertEqual(initials("3d printer"), "DP")

    def test_only_separators(self):
        self.assertEqual(initials("- -"), "")

    def test_part_without_letters_contributes_nothing(self):
        self.assertEqual(initials("ann 42 lee"), "AL")

    def test_upper_case_may_be_several_characters(self):
        self.assertEqual(initials("ßa"), "SS")

    def test_tab_is_not_a_separator(self):
        self.assertEqual(initials("jean\tluc"), "J")


if __name__ == "__main__":
    unittest.main()
