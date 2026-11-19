"""Tests for textkit.strings: one TestCase class per public function."""

import unittest

from textkit.strings import slugify, squeeze


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_runs_of_separators_become_one_dash(self):
        self.assertEqual(slugify("a  --  b...c"), "a-b-c")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case__name"), "snake-case-name")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--  Hello  --"), "hello")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Version 2.0 RC1"), "version-2-0-rc1")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        self.assertEqual(slugify("Ñandú"), "and")

    def test_nfd_input(self):
        self.assertEqual(slugify("Ñandú"), "nandu")

    def test_non_ascii_digits_and_letters_removed(self):
        # str.isalnum would accept these; slugify must not.
        self.assertEqual(slugify("a١b ²c"), "ab-c")

    def test_empty(self):
        self.assertEqual(slugify(""), "")

    def test_punctuation_only(self):
        self.assertEqual(slugify("!!!"), "")

    def test_non_ascii_only(self):
        self.assertEqual(slugify("日本語"), "")


if __name__ == "__main__":
    unittest.main()
