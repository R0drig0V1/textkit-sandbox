import unicodedata
import unittest

from textkit.strings import slugify, squeeze, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class TruncateTest(unittest.TestCase):
    def test_fits_is_unchanged(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_exact_width_is_unchanged(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cut_keeps_start_and_is_exactly_width(self):
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 6, suffix="~"), "hello~")

    def test_empty_suffix_is_plain_cut(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_zero_width_empty_suffix(self):
        self.assertEqual(truncate("x", 0, suffix=""), "")

    def test_empty_text(self):
        self.assertEqual(truncate("", 3), "")

    def test_counts_code_points(self):
        self.assertEqual(truncate("ñandú", 5), "ñandú")
        self.assertEqual(truncate("ñandú!", 5), "ña...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("hi", 2)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")


class SlugifyTest(unittest.TestCase):
    def test_punctuation_and_spaces_become_one_hyphen(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_strips_hyphens_at_both_ends(self):
        self.assertEqual(slugify("--a b--"), "a-b")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case__name"), "snake-case-name")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Top 10 Tips"), "top-10-tips")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("na\u00efve"), "nave")

    def test_nfc_input_drops_precomposed_letters(self):
        nfc = unicodedata.normalize("NFC", "Ñandú")
        self.assertEqual(slugify(nfc), "and")

    def test_nfd_input_keeps_base_letters(self):
        nfd = unicodedata.normalize("NFD", "Ñandú")
        self.assertEqual(slugify(nfd), "nandu")

    def test_empty_and_punctuation_only_give_empty(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")


if __name__ == "__main__":
    unittest.main()
