import unicodedata
import unittest

from textkit.strings import squeeze, truncate
from textkit.strings import strip_accents


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class TruncateTest(unittest.TestCase):
    def test_returns_text_unchanged_when_shorter_than_width(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_returns_text_unchanged_when_exactly_width(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cuts_to_exact_width_with_default_suffix(self):
        result = truncate("Hello, World!", 8)
        self.assertEqual(result, "Hello...")
        self.assertEqual(len(result), 8)

    def test_custom_suffix(self):
        self.assertEqual(truncate("abcdefghij", 5, suffix="~"), "abcd~")

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("abcdefghij", 4, suffix=""), "abcd")

    def test_width_equal_to_suffix_length_gives_only_suffix(self):
        self.assertEqual(truncate("abcdefghij", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("abc", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_counts_code_points(self):
        self.assertEqual(truncate("ñandú", 5), "ñandú")
        self.assertEqual(truncate("ñandúes", 6), "ñan...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("abcdefghij", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("ab", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("abc", -1, suffix="")


class StripAccentsTest(unittest.TestCase):
    def test_plan_example(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_nfc_and_nfd_input_give_the_same_result(self):
        for form in ("NFC", "NFD"):
            with self.subTest(form=form):
                text = unicodedata.normalize(form, "Ñandú crème brûlée")
                self.assertEqual(strip_accents(text), "Nandu creme brulee")

    def test_upper_case_and_other_scripts(self):
        self.assertEqual(strip_accents("ÉCOLE Ångström"), "ECOLE Angstrom")
        self.assertEqual(strip_accents("άέή"), "αεη")

    def test_stacked_marks(self):
        self.assertEqual(strip_accents("ệ"), "e")
        self.assertEqual(strip_accents("a\u0301\u0323"), "a")

    def test_ascii_and_empty_unchanged(self):
        self.assertEqual(strip_accents(""), "")
        self.assertEqual(strip_accents("Hello, World! 123"), "Hello, World! 123")

    def test_letters_without_decomposition_are_kept(self):
        self.assertEqual(strip_accents("øłßæ"), "øłßæ")

    def test_compatibility_characters_are_kept(self):
        self.assertEqual(strip_accents("ﬁ²Ａ"), "ﬁ²Ａ")

    def test_hangul_is_recomposed(self):
        self.assertEqual(strip_accents("한국어"), "한국어")


if __name__ == "__main__":
    unittest.main()
