"""Tests for textkit.strings: one TestCase class per public function."""

import unittest

from textkit.strings import slugify, squeeze, truncate


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


class TruncateTest(unittest.TestCase):
    def test_text_that_fits_is_unchanged(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_text_exactly_width_is_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cut_result_is_exactly_width_with_suffix(self):
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_cut_keeps_the_start(self):
        self.assertEqual(truncate("abcdefghij", 6, suffix="~"), "abcde~")

    def test_custom_empty_suffix(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("hello", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_counts_code_points(self):
        self.assertEqual(truncate("ñandú", 5), "ñandú")
        self.assertEqual(truncate("ñandú y más", 6), "ñan...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("hi", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_with_empty_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")


if __name__ == "__main__":
    unittest.main()
