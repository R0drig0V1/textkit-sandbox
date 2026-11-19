"""Tests for textkit.strings, one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import slugify, squeeze, strip_accents, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


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
        self.assertEqual(truncate("abcdefgh", 6, suffix="~"), "abcde~")

    def test_custom_empty_suffix(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("", 2)
        with self.assertRaises(ValueError):
            truncate("ab", 2)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello", -1, suffix="")

    def test_zero_width_with_empty_suffix(self):
        self.assertEqual(truncate("hello", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_counts_code_points(self):
        # "e" + combining acute is two code points, so it does not fit in width 1.
        self.assertEqual(truncate("e\u0301x", 2, suffix=""), "e\u0301")
        self.assertEqual(truncate("\u00f1and\u00fa", 5), "\u00f1and\u00fa")


class StripAccentsTest(unittest.TestCase):
    def test_removes_marks_nfc_input(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_removes_marks_nfd_input(self):
        self.assertEqual(strip_accents(unicodedata.normalize("NFD", "Ñandú")), "Nandu")

    def test_several_marks(self):
        self.assertEqual(strip_accents("naïve café Ångström"), "naive cafe Angstrom")

    def test_stacked_marks(self):
        self.assertEqual(strip_accents("e\u0301\u0302"), "e")

    def test_plain_ascii_unchanged(self):
        self.assertEqual(strip_accents("Hello, World! 123"), "Hello, World! 123")

    def test_empty(self):
        self.assertEqual(strip_accents(""), "")

    def test_letters_without_decomposition_kept(self):
        self.assertEqual(strip_accents("ßøæ"), "ßøæ")

    def test_lone_combining_mark_removed(self):
        self.assertEqual(strip_accents("\u0301"), "")


class SlugifyTest(unittest.TestCase):
    def test_basic_example(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_lower_cases(self):
        self.assertEqual(slugify("ABC Def"), "abc-def")

    def test_run_of_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  --  b...c"), "a-b-c")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case__name"), "snake-case-name")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--  hello  --"), "hello")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Version 2.0"), "version-2-0")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        text = unicodedata.normalize("NFC", "Ñandú")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input(self):
        text = unicodedata.normalize("NFD", "Ñandú")
        self.assertEqual(slugify(text), "nandu")

    def test_non_ascii_that_lowercases_to_ascii_is_removed(self):
        # KELVIN SIGN lower-cases to ASCII "k"; it must be removed before lower-casing.
        self.assertEqual(slugify("K"), "")
        self.assertEqual(slugify("İstanbul"), "stanbul")

    def test_non_ascii_alphanumerics_are_not_kept(self):
        self.assertEqual(slugify("a²b ٣"), "ab")

    def test_empty(self):
        self.assertEqual(slugify(""), "")

    def test_punctuation_only(self):
        self.assertEqual(slugify("!!!"), "")


if __name__ == "__main__":
    unittest.main()
