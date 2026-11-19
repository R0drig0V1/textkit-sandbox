"""Tests for textkit.strings: one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import is_palindrome, slugify, squeeze, strip_accents, truncate, wrap


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


class IsPalindromeTest(unittest.TestCase):
    def test_simple_palindromes(self):
        self.assertTrue(is_palindrome("racecar"))
        self.assertTrue(is_palindrome("a"))

    def test_not_a_palindrome(self):
        self.assertFalse(is_palindrome("hello"))
        self.assertFalse(is_palindrome("ab"))

    def test_ignores_case_spaces_and_punctuation(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama"))
        self.assertTrue(is_palindrome("Was it a car or a cat I saw?"))

    def test_ignores_accents_nfc_and_nfd(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panam\u00e1"))
        self.assertTrue(is_palindrome("E\u0301te\u0301"))
        self.assertTrue(is_palindrome("\u00c9t\u00e9"))

    def test_digits_count(self):
        self.assertTrue(is_palindrome("12321"))
        self.assertTrue(is_palindrome("1a1"))
        self.assertFalse(is_palindrome("123"))
        self.assertFalse(is_palindrome("a1b"))

    def test_casefold_not_just_lower(self):
        # casefold() turns "\u00df" into "ss", which lower() would not.
        self.assertTrue(is_palindrome("\u00dfS"))

    def test_non_ascii_letters_count(self):
        self.assertTrue(is_palindrome("\u00f8a\u00f8"))
        self.assertFalse(is_palindrome("\u00f8a\u0142"))

    def test_empty_and_no_alphanumerics_are_palindromes(self):
        self.assertTrue(is_palindrome(""))
        self.assertTrue(is_palindrome("   "))
        self.assertTrue(is_palindrome("!?, .;"))
        self.assertTrue(is_palindrome("\u0301"))


class WrapTest(unittest.TestCase):
    def test_fills_lines_greedily(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("ab cd", 5), ["ab cd"])

    def test_one_over_width_breaks(self):
        self.assertEqual(wrap("ab cde", 5), ["ab", "cde"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b     c", 80), ["a b c"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 80), ["a b"])

    def test_lines_never_contain_separating_space(self):
        for line in wrap("aa bb  cc   dd    ee", 5):
            self.assertEqual(line, line.strip())
            self.assertLessEqual(len(line), 5)

    def test_empty(self):
        self.assertEqual(wrap("", 10), [])

    def test_spaces_only(self):
        self.assertEqual(wrap("     ", 10), [])

    def test_long_word_gets_own_line(self):
        self.assertEqual(wrap("a abcdefghij b", 4), ["a", "abcdefghij", "b"])

    def test_long_word_alone(self):
        self.assertEqual(wrap("abcdefghij", 3), ["abcdefghij"])

    def test_width_one(self):
        self.assertEqual(wrap("a b c", 1), ["a", "b", "c"])

    def test_width_zero_raises(self):
        with self.assertRaises(ValueError):
            wrap("a b", 0)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            wrap("a b", -3)

    def test_width_checked_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            wrap("", 0)

    # ADR 0003: existing newlines are word separators, not kept.
    def test_newline_is_a_separator(self):
        self.assertEqual(wrap("a\nb", 80), ["a b"])

    def test_blank_lines_are_not_kept(self):
        self.assertEqual(wrap("one\n\ntwo", 80), ["one two"])

    def test_crlf_and_tabs_are_separators(self):
        self.assertEqual(wrap("a\r\nb\tc", 80), ["a b c"])

    def test_newlines_rewrapped_to_width(self):
        self.assertEqual(wrap("aa\nbb\ncc", 5), ["aa bb", "cc"])

    def test_no_line_contains_newline(self):
        for line in wrap("x\ny z\n\nw\n", 3):
            self.assertNotIn("\n", line)

    def test_newline_only(self):
        self.assertEqual(wrap("\n\n", 10), [])


if __name__ == "__main__":
    unittest.main()
