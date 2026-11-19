"""Tests for textkit.strings: one TestCase class per public function."""

import unittest

from textkit.strings import is_palindrome, slug_title, slugify, squeeze, strip_accents, truncate, wrap


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


class StripAccentsTest(unittest.TestCase):
    def test_removes_marks_from_nfc_input(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_removes_marks_from_nfd_input(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_several_marks_on_one_letter(self):
        # Vietnamese "ệ" carries two marks (circumflex and dot below).
        self.assertEqual(strip_accents("Việt"), "Viet")

    def test_plain_ascii_is_unchanged(self):
        self.assertEqual(strip_accents("Hello, World!"), "Hello, World!")

    def test_letters_without_decomposition_are_kept(self):
        self.assertEqual(strip_accents("ø ß æ"), "ø ß æ")

    def test_hangul_syllables_stay_composed(self):
        self.assertEqual(strip_accents("\ud55c\uae00"), "\ud55c\uae00")

    def test_empty_string(self):
        self.assertEqual(strip_accents(""), "")


class WrapTest(unittest.TestCase):
    def test_packs_words_greedily(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("abc def", 7), ["abc def"])
        self.assertEqual(wrap("abc def", 6), ["abc", "def"])

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(wrap("a extraordinary b", 5), ["a", "extraordinary", "b"])

    def test_long_word_alone(self):
        self.assertEqual(wrap("extraordinary", 3), ["extraordinary"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b     c", 80), ["a b c"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 80), ["a b"])

    def test_empty_and_blank_text(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("     ", 5), [])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.subTest(width=width):
                with self.assertRaises(ValueError):
                    wrap("abc", width)
        with self.assertRaises(ValueError):
            wrap("", 0)

    def test_width_one(self):
        self.assertEqual(wrap("a b cd", 1), ["a", "b", "cd"])

    def test_lines_never_contain_the_separating_space(self):
        for line in wrap("one two three four five six", 7):
            self.assertFalse(line.startswith(" ") or line.endswith(" "), line)
            self.assertLessEqual(len(line), 7)

    def test_newlines_are_separators(self):
        # docs/decisions/0005-wrap-existing-newlines.md: newlines are reflowed like spaces.
        self.assertEqual(wrap("one\ntwo three", 80), ["one two three"])
        self.assertEqual(wrap("one\n\ntwo", 3), ["one", "two"])
        self.assertEqual(wrap("a\r\nb\rc", 80), ["a b c"])

    def test_other_whitespace_is_a_separator(self):
        self.assertEqual(wrap("a\tb\u00a0c", 80), ["a b c"])

    def test_no_line_contains_a_newline(self):
        for line in wrap("para one\n\npara two\n", 4):
            self.assertNotIn("\n", line)


class SlugTitleTest(unittest.TestCase):
    def test_cut_inside_a_word_keeps_the_partial_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_cut_after_a_separator_drops_the_trailing_dash(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_slug_that_fits_is_returned_whole(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")
        self.assertEqual(slug_title("Hello, World!", 50), "hello-world")

    def test_zero_max_len_gives_empty(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_empty_slug_gives_empty(self):
        self.assertEqual(slug_title("!!!", 5), "")
        self.assertEqual(slug_title("", 0), "")

    def test_never_longer_than_max_len_nor_ending_in_dash(self):
        for max_len in range(0, 20):
            result = slug_title("A b  c--d, e!", max_len)
            self.assertLessEqual(len(result), max_len)
            self.assertFalse(result.endswith("-"))

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("Hello, World!", -1)
        with self.assertRaises(ValueError):
            slug_title("", -1)


class IsPalindromeTest(unittest.TestCase):
    def test_simple_palindrome(self):
        self.assertTrue(is_palindrome("level"))

    def test_not_a_palindrome(self):
        self.assertFalse(is_palindrome("hello"))

    def test_ignores_case_spaces_and_punctuation(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama!"))

    def test_ignores_accents_in_nfc_input(self):
        self.assertTrue(is_palindrome("Ésé"))
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panamá"))

    def test_ignores_accents_in_nfd_input(self):
        self.assertTrue(is_palindrome("E\u0301se\u0301"))

    def test_accented_non_palindrome(self):
        self.assertFalse(is_palindrome("Ñandú"))

    def test_digits_count(self):
        self.assertTrue(is_palindrome("12321"))
        self.assertFalse(is_palindrome("123"))
        self.assertFalse(is_palindrome("1a2"))

    def test_casefold_expands_sharp_s(self):
        # casefold turns "ß" into "ss"; lower() would leave it as one character.
        self.assertTrue(is_palindrome("Straße ssarts"))

    def test_mark_added_by_casefold_is_ignored(self):
        # "İ" casefolds to "i" + U+0307 after strip_accents has run.
        self.assertTrue(is_palindrome("İi"))

    def test_non_ascii_letters_count(self):
        self.assertTrue(is_palindrome("øaø"))
        self.assertFalse(is_palindrome("øa"))

    def test_empty_string(self):
        self.assertTrue(is_palindrome(""))

    def test_no_alphanumerics(self):
        self.assertTrue(is_palindrome("!!! ,. ?"))


if __name__ == "__main__":
    unittest.main()
