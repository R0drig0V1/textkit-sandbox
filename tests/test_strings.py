"""Tests for textkit.strings: one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import (
    is_palindrome,
    slug_title,
    slugify,
    squeeze,
    strip_accents,
    truncate,
    wrap,
)


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


class TruncateTest(unittest.TestCase):
    def test_text_that_fits_is_unchanged(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_text_exactly_width_is_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cut_keeps_start_and_result_is_exactly_width(self):
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 6, suffix="~"), "hello~")

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("x", 0, suffix=""), "")

    def test_empty_text(self):
        self.assertEqual(truncate("", 3), "")

    def test_width_counts_code_points(self):
        self.assertEqual(truncate("ñandú y más", 6), "ñan...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("hi", 2)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")


class StripAccentsTest(unittest.TestCase):
    def test_spec_example(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_nfc_and_nfd_input_give_the_same_result(self):
        nfc = unicodedata.normalize("NFC", "Ñandú café")
        nfd = unicodedata.normalize("NFD", "Ñandú café")
        self.assertNotEqual(nfc, nfd)
        self.assertEqual(strip_accents(nfc), "Nandu cafe")
        self.assertEqual(strip_accents(nfd), "Nandu cafe")

    def test_several_marks_on_one_letter(self):
        # Vietnamese "ệ" carries a circumflex and a dot below.
        self.assertEqual(strip_accents("Việt"), "Viet")

    def test_letters_without_decomposition_are_kept(self):
        self.assertEqual(strip_accents("øß"), "øß")

    def test_text_without_marks_is_not_decomposed(self):
        self.assertEqual(strip_accents("한국어 日本"), "한국어 日本")

    def test_ascii_and_empty_unchanged(self):
        self.assertEqual(strip_accents("Hello, World! 123"), "Hello, World! 123")
        self.assertEqual(strip_accents(""), "")


class SlugTitleTest(unittest.TestCase):
    def test_cut_inside_a_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_trailing_dash_after_cut_is_stripped(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_slug_that_fits_is_unchanged(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")
        self.assertEqual(slug_title("Hello, World!", 50), "hello-world")

    def test_max_len_zero_gives_empty(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_never_ends_in_dash_and_respects_max_len(self):
        text = "a b-c  d__e Hello, World!"
        for max_len in range(0, 30):
            result = slug_title(text, max_len)
            self.assertLessEqual(len(result), max_len)
            self.assertFalse(result.endswith("-"))

    def test_matches_truncate_of_slugify(self):
        text = "Version 2.0 Release"
        for max_len in range(0, 25):
            expected = truncate(slugify(text), max_len, suffix="").rstrip("-")
            self.assertEqual(slug_title(text, max_len), expected)

    def test_empty_slug(self):
        self.assertEqual(slug_title("!!!", 5), "")
        self.assertEqual(slug_title("", 5), "")

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("hello", -1)

    def test_negative_max_len_raises_for_empty_text(self):
        with self.assertRaises(ValueError):
            slug_title("", -1)


class WrapTest(unittest.TestCase):
    def test_basic_example(self):
        self.assertEqual(
            wrap("the quick brown fox jumps", 10), ["the quick", "brown fox", "jumps"]
        )

    def test_line_of_exactly_width_fits(self):
        self.assertEqual(wrap("ab cd ef", 5), ["ab cd", "ef"])

    def test_text_that_fits_is_one_line(self):
        self.assertEqual(wrap("hello world", 11), ["hello world"])

    def test_lines_never_exceed_width_for_short_words(self):
        text = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do"
        for width in range(11, 30):
            with self.subTest(width=width):
                lines = wrap(text, width)
                self.assertTrue(all(len(line) <= width for line in lines))
                self.assertEqual(" ".join(lines), text)

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(
            wrap("a extraordinarily b", 5), ["a", "extraordinarily", "b"]
        )

    def test_long_word_is_not_split(self):
        self.assertEqual(wrap("abcdef", 3), ["abcdef"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b     c", 3), ["a b", "c"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 10), ["a b"])

    def test_lines_never_contain_separating_space(self):
        for line in wrap("aa bb cc dd ee", 4):
            self.assertFalse(line.startswith(" ") or line.endswith(" "))

    def test_empty_string(self):
        self.assertEqual(wrap("", 5), [])

    def test_whitespace_only(self):
        self.assertEqual(wrap("   \n  ", 5), [])

    def test_newlines_are_separators(self):
        # ADR 0003: existing line breaks are reflowed like spaces.
        self.assertEqual(wrap("one\ntwo three\n\nfour", 9), ["one two", "three", "four"])
        self.assertEqual(wrap("a\r\nb", 3), ["a b"])

    def test_other_whitespace_is_a_separator(self):
        self.assertEqual(wrap("a\tb\u00a0c", 10), ["a b c"])

    def test_no_line_contains_a_newline(self):
        for line in wrap("x\ny\nz " * 5, 4):
            self.assertNotIn("\n", line)

    def test_width_one(self):
        self.assertEqual(wrap("a b cd", 1), ["a", "b", "cd"])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.subTest(width=width):
                with self.assertRaises(ValueError):
                    wrap("text", width)

    def test_width_below_one_raises_for_empty_text(self):
        with self.assertRaises(ValueError):
            wrap("", 0)


class IsPalindromeTest(unittest.TestCase):
    def test_simple_palindrome(self):
        self.assertTrue(is_palindrome("racecar"))
        self.assertTrue(is_palindrome("abba"))

    def test_not_a_palindrome(self):
        self.assertFalse(is_palindrome("hello"))
        self.assertFalse(is_palindrome("ab"))

    def test_ignores_case(self):
        self.assertTrue(is_palindrome("RaceCar"))

    def test_ignores_spaces_and_punctuation(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama"))
        self.assertTrue(is_palindrome("Was it a car or a cat I saw?"))

    def test_ignores_accents(self):
        self.assertTrue(is_palindrome("Dábale arroz a la zorra el abad"))
        self.assertTrue(is_palindrome("Ánà"))

    def test_nfc_and_nfd_input_agree(self):
        text = "Dábale arroz a la zorra el abad"
        nfd = unicodedata.normalize("NFD", text)
        self.assertNotEqual(text, nfd)
        self.assertTrue(is_palindrome(nfd))

    def test_digits_count(self):
        self.assertTrue(is_palindrome("12321"))
        self.assertTrue(is_palindrome("1a1"))
        self.assertFalse(is_palindrome("123"))
        self.assertFalse(is_palindrome("a1"))

    def test_casefold_not_lower(self):
        # "ß".casefold() == "ss", so "ßs" compares as "sss".
        self.assertTrue(is_palindrome("ßs"))
        self.assertTrue(is_palindrome("SSß"))

    def test_non_ascii_letters_without_decomposition_are_kept(self):
        self.assertTrue(is_palindrome("øaø"))
        self.assertFalse(is_palindrome("øo"))

    def test_empty_and_no_alphanumerics_are_true(self):
        self.assertTrue(is_palindrome(""))
        self.assertTrue(is_palindrome("!!!"))
        self.assertTrue(is_palindrome("  ,.-  "))

    def test_single_character(self):
        self.assertTrue(is_palindrome("x"))


if __name__ == "__main__":
    unittest.main()
