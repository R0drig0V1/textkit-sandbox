"""Tests for textkit.strings: one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import slugify, squeeze, strip_accents, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        text = unicodedata.normalize("NFC", "Ñandú")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input(self):
        text = unicodedata.normalize("NFD", "Ñandú")
        self.assertEqual(slugify(text), "nandu")

    def test_empty(self):
        self.assertEqual(slugify(""), "")

    def test_punctuation_only(self):
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_runs_collapse_and_ends_strip(self):
        self.assertEqual(slugify("  --A  _ b--  "), "a-b")

    def test_digits_kept(self):
        self.assertEqual(slugify("Version 2.0"), "version-2-0")


class TruncateTest(unittest.TestCase):
    def test_text_that_fits_is_unchanged(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_text_exactly_width_is_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_long_text_is_cut_to_exact_width_with_suffix(self):
        result = truncate("Hello, World!", 8)
        self.assertEqual(result, "Hello...")
        self.assertEqual(len(result), 8)

    def test_one_over_width(self):
        self.assertEqual(truncate("abcdef", 5), "ab...")

    def test_custom_suffix(self):
        self.assertEqual(truncate("Hello, World!", 6, suffix="~"), "Hello~")

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("Hello, World!", 5, suffix=""), "Hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("Hello", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("x", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_empty_text(self):
        self.assertEqual(truncate("", 5), "")

    def test_counts_code_points(self):
        self.assertEqual(truncate("ñandú", 5), "ñandú")
        self.assertEqual(truncate("ñandúes", 5), "ña...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("Hello, World!", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("ab", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")


class StripAccentsTest(unittest.TestCase):
    def test_removes_accents_from_nfc_input(self):
        self.assertEqual(strip_accents("\u00d1and\u00fa"), "Nandu")

    def test_removes_accents_from_nfd_input(self):
        self.assertEqual(strip_accents("N\u0303andu\u0301"), "Nandu")

    def test_mixed_text(self):
        self.assertEqual(
            strip_accents("Cr\u00e8me br\u00fbl\u00e9e, na\u00efve!"), "Creme brulee, naive!"
        )

    def test_ascii_and_empty_unchanged(self):
        self.assertEqual(strip_accents("Hello, World! 123"), "Hello, World! 123")
        self.assertEqual(strip_accents(""), "")

    def test_lone_combining_mark_removed(self):
        self.assertEqual(strip_accents("a\u0301\u0308"), "a")
        self.assertEqual(strip_accents("\u0301"), "")

    def test_letters_without_decomposition_kept(self):
        self.assertEqual(strip_accents("\u00f8\u0142\u00df"), "\u00f8\u0142\u00df")

    def test_hangul_recomposed(self):
        self.assertEqual(strip_accents("\ud55c\uad6d\uc5b4"), "\ud55c\uad6d\uc5b4")

    def test_result_is_nfc(self):
        result = strip_accents("e\u0301 \u00e9")
        self.assertEqual(result, "e e")
        self.assertEqual(result, unicodedata.normalize("NFC", result))


if __name__ == "__main__":
    unittest.main()
