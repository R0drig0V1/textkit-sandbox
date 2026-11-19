import unicodedata
import unittest

from textkit.strings import slugify, squeeze, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_punctuation_and_case(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        self.assertEqual(slugify(unicodedata.normalize("NFC", "Ñandú")), "and")

    def test_nfd_input(self):
        self.assertEqual(slugify(unicodedata.normalize("NFD", "Ñandú")), "nandu")

    def test_empty_and_punctuation_only(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_and_whitespace_runs_become_one_dash(self):
        self.assertEqual(slugify("snake_case  and__more\t\nlines"), "snake-case-and-more-lines")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("  -_ x _-  "), "x")

    def test_digits_kept(self):
        self.assertEqual(slugify("Release 2.0"), "release-2-0")

    def test_non_ascii_digits_and_letters_removed(self):
        # Arabic-Indic digit, superscript two, Kelvin sign (lower() would give ASCII "k").
        self.assertEqual(slugify("a\u0663b\u00b2c\u212a"), "abc")

    def test_only_non_ascii(self):
        self.assertEqual(slugify("日本語"), "")


class TruncateTest(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(truncate("abc", 10), "abc")

    def test_exact_fit_unchanged(self):
        self.assertEqual(truncate("abcdef", 6), "abcdef")

    def test_cut_keeps_start_and_has_exact_width(self):
        result = truncate("Hello, World!", 8)
        self.assertEqual(result, "Hello...")
        self.assertEqual(len(result), 8)

    def test_one_over_width(self):
        self.assertEqual(truncate("abcdefg", 6), "abc...")

    def test_custom_suffix(self):
        self.assertEqual(truncate("abcdefghij", 5, suffix="~"), "abcd~")

    def test_width_equal_to_suffix_gives_suffix_only(self):
        self.assertEqual(truncate("abcdef", 3), "...")

    def test_width_equal_to_suffix_text_fits(self):
        self.assertEqual(truncate("ab", 3), "ab")

    def test_empty_suffix_is_plain_cut(self):
        self.assertEqual(truncate("abcdef", 4, suffix=""), "abcd")

    def test_empty_suffix_width_zero(self):
        self.assertEqual(truncate("abc", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_empty_text(self):
        self.assertEqual(truncate("", 3), "")

    def test_width_below_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("abcdef", 2)

    def test_width_below_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("ab", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_with_empty_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("abc", -1, suffix="")

    def test_counts_code_points(self):
        self.assertEqual(truncate("\u00f1and\u00fa!", 5), "\u00f1a...")


if __name__ == "__main__":
    unittest.main()
