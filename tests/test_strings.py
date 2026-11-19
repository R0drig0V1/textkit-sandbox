"""Tests for textkit.strings."""

import unicodedata
import unittest

from textkit.strings import slugify, squeeze, strip_accents, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_example_from_the_plan(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_punctuation_gives_empty_string(self):
        self.assertEqual(slugify("!?.,;:-_ \t\n"), "")

    def test_strips_leading_and_trailing_separators(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("  ...Hello World!!!  "), "hello-world")

    def test_collapses_every_separator_run_to_one_dash(self):
        self.assertEqual(slugify("a  -_- b"), "a-b")
        self.assertEqual(slugify("a\tb\nc"), "a-b-c")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Top 10 Tips"), "top-10-tips")
        self.assertEqual(slugify("2024-01-02"), "2024-01-02")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_already_a_slug_is_unchanged(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_dropped_non_ascii_does_not_separate_words(self):
        self.assertEqual(slugify("aéb"), "ab")
        self.assertEqual(slugify("café au lait"), "caf-au-lait")
        self.assertEqual(slugify("a—b"), "ab")  # em dash is non-ASCII, so dropped

    def test_only_non_ascii_gives_empty_string(self):
        self.assertEqual(slugify("日本語"), "")

    def test_non_ascii_next_to_separators_leaves_no_stray_dash(self):
        self.assertEqual(slugify("é Hello é"), "hello")

    def test_non_ascii_with_ascii_lower_case_is_dropped(self):
        # The Kelvin sign lower-cases to ASCII "k"; it is dropped before lower-casing.
        self.assertEqual(slugify("K"), "")
        self.assertEqual(slugify("5K run"), "5-run")


class TruncateTest(unittest.TestCase):
    def test_fits_exactly_is_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_shorter_than_width_is_unchanged(self):
        self.assertEqual(truncate("hi", 5), "hi")

    def test_one_over_is_cut_to_width(self):
        result = truncate("hello!", 5)
        self.assertEqual(result, "he...")
        self.assertEqual(len(result), 5)

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 6, suffix="~"), "hello~")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello", 3), "...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaisesRegex(ValueError, "len\\(suffix\\)"):
            truncate("hello", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("ab", 2)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello", -1)
        with self.assertRaises(ValueError):
            truncate("hello", -1, suffix="")

    def test_empty_text(self):
        self.assertEqual(truncate("", 5), "")
        self.assertEqual(truncate("", 0, suffix=""), "")


class StripAccentsTest(unittest.TestCase):
    def test_precomposed(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")
        self.assertEqual(strip_accents("crème brûlée, façade"), "creme brulee, facade")

    def test_already_decomposed(self):
        decomposed = unicodedata.normalize("NFD", "Ñandú")
        self.assertNotEqual(decomposed, "Ñandú")  # guard: the input really is decomposed
        self.assertEqual(strip_accents(decomposed), "Nandu")
        # A stray combining mark on its own is removed too.
        self.assertEqual(strip_accents("á̈b"), "ab")

    def test_empty(self):
        self.assertEqual(strip_accents(""), "")

    def test_no_accents_unchanged(self):
        for text in ("Hello, World! 123", "  spaces\tand\nlines ", "ø ł đ ß"):
            with self.subTest(text=text):
                self.assertEqual(strip_accents(text), text)

    def test_compatibility_characters_kept(self):
        # NFD, not NFKD: ligatures, superscripts and full-width letters are not accents.
        self.assertEqual(strip_accents("ﬁ²Ａ"), "ﬁ²Ａ")

    def test_non_latin(self):
        self.assertEqual(strip_accents("Ελλάδα"), "Ελλαδα")
        self.assertEqual(strip_accents("йод"), "иод")
        # Scripts with no combining marks come back unchanged, Hangul included
        # (NFD splits it into jamo; the NFC step puts it back together).
        for text in ("Москва", "東京", "한국어", "مرحبا"):
            with self.subTest(text=text):
                self.assertEqual(strip_accents(text), text)


if __name__ == "__main__":
    unittest.main()
