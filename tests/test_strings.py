"""Tests for textkit.strings: one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import slugify, squeeze


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_basic_example(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_lower_cases(self):
        self.assertEqual(slugify("ABC def"), "abc-def")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Version 2.0 Release"), "version-2-0-release")

    def test_run_of_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  --  b...c"), "a-b-c")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case__name"), "snake-case-name")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--hello--"), "hello")
        self.assertEqual(slugify("  (hello)  "), "hello")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_punctuation_only(self):
        self.assertEqual(slugify("!!!"), "")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        text = unicodedata.normalize("NFC", "Ñandú")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input(self):
        text = unicodedata.normalize("NFD", "Ñandú")
        self.assertEqual(slugify(text), "nandu")

    def test_non_ascii_digits_and_letters_are_not_kept(self):
        # str.isalnum would accept these; the slug must stay ASCII.
        self.assertEqual(slugify("a١b²c"), "abc")
        self.assertEqual(slugify("日本 test"), "test")

    def test_result_is_already_a_slug(self):
        self.assertEqual(slugify("hello-world"), "hello-world")


if __name__ == "__main__":
    unittest.main()
