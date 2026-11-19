"""Tests for textkit.strings: one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import slug_title, slugify, squeeze, strip_accents, truncate


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


if __name__ == "__main__":
    unittest.main()
