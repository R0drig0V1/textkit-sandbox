import unittest

import unicodedata

from textkit.strings import slugify, squeeze, strip_accents, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")



class SlugifyTest(unittest.TestCase):
    def test_basic_example(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        text = unicodedata.normalize("NFC", "Ñandú")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input(self):
        text = unicodedata.normalize("NFD", "Ñandú")
        self.assertEqual(slugify(text), "nandu")

    def test_empty_and_punctuation_only(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_and_runs_become_one_hyphen(self):
        self.assertEqual(slugify("snake_case  --  name"), "snake-case-name")

    def test_strips_hyphens_at_both_ends(self):
        self.assertEqual(slugify("--Already-Slug--"), "already-slug")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Version 2.0"), "version-2-0")

    def test_non_ascii_digits_and_letters_removed(self):
        # str.isalnum would keep these; the ASCII-only rule drops them.
        self.assertEqual(slugify("a٣b été"), "ab-t")


class TruncateTest(unittest.TestCase):
    def test_text_that_fits_is_unchanged(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_text_exactly_width_is_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cut_keeps_start_and_result_is_width_long(self):
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 6, suffix="~"), "hello~")

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("hello", 0, suffix=""), "")

    def test_width_below_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_below_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("ab", 2)
        with self.assertRaises(ValueError):
            truncate("", 0, suffix="...")

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")

    def test_counts_code_points(self):
        self.assertEqual(truncate("Ñandú!", 5, suffix="."), "Ñand.")


class StripAccentsTest(unittest.TestCase):
    def test_plan_example(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_nfd_input(self):
        self.assertEqual(strip_accents(unicodedata.normalize("NFD", "Ñandú")), "Nandu")

    def test_several_marks_on_one_letter(self):
        # "ệ" carries a circumflex and a dot below.
        self.assertEqual(strip_accents("Tiếng Việt"), "Tieng Viet")

    def test_plain_ascii_unchanged(self):
        self.assertEqual(strip_accents("Hello, World!"), "Hello, World!")

    def test_empty(self):
        self.assertEqual(strip_accents(""), "")

    def test_letters_without_decomposition_kept(self):
        self.assertEqual(strip_accents("øłß"), "øłß")

    def test_lone_combining_mark_removed(self):
        self.assertEqual(strip_accents("a\u0301\u0308"), "a")

    def test_hangul_stays_composed(self):
        self.assertEqual(strip_accents("한국어"), "한국어")


if __name__ == "__main__":
    unittest.main()
