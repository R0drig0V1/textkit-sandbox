"""Tests for textkit.strings: one TestCase class per public function."""

import unittest

from textkit.strings import slugify, squeeze


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_joins_words(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input_drops_precomposed_letters(self):
        self.assertEqual(slugify("Ñandú"), "and")  # "Ñandú", NFC as typed

    def test_nfd_input_keeps_base_letters(self):
        self.assertEqual(slugify("Ñandú"), "nandu")  # "Ñandú", NFD

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_separators(self):
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_run_of_mixed_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  _-!? b"), "a-b")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--Hello--"), "hello")

    def test_digits_kept(self):
        self.assertEqual(slugify("Python 3.9"), "python-3-9")

    def test_non_ascii_removed_before_lowercasing(self):
        # U+212A KELVIN SIGN lower-cases to ASCII "k"; it must be removed, not kept.
        self.assertEqual(slugify("5K run"), "5-run")


if __name__ == "__main__":
    unittest.main()
