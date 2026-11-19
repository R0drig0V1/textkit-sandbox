import unittest

import unicodedata

from textkit.strings import squeeze, strip_accents, truncate


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


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
        self.assertEqual(truncate("abcdefgh", 6, suffix="~"), "abcde~")

    def test_custom_empty_suffix(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("", 2)
        with self.assertRaises(ValueError):
            truncate("ab", 2)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello", -1, suffix="")

    def test_zero_width_with_empty_suffix(self):
        self.assertEqual(truncate("hello", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_counts_code_points(self):
        # "e" + combining acute is two code points, so it does not fit in width 1.
        self.assertEqual(truncate("e\u0301x", 2, suffix=""), "e\u0301")
        self.assertEqual(truncate("\u00f1and\u00fa", 5), "\u00f1and\u00fa")


class StripAccentsTest(unittest.TestCase):
    def test_removes_marks_nfc_input(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_removes_marks_nfd_input(self):
        self.assertEqual(strip_accents(unicodedata.normalize("NFD", "Ñandú")), "Nandu")

    def test_several_marks(self):
        self.assertEqual(strip_accents("naïve café Ångström"), "naive cafe Angstrom")

    def test_stacked_marks(self):
        self.assertEqual(strip_accents("e\u0301\u0302"), "e")

    def test_plain_ascii_unchanged(self):
        self.assertEqual(strip_accents("Hello, World! 123"), "Hello, World! 123")

    def test_empty(self):
        self.assertEqual(strip_accents(""), "")

    def test_letters_without_decomposition_kept(self):
        self.assertEqual(strip_accents("ßøæ"), "ßøæ")

    def test_lone_combining_mark_removed(self):
        self.assertEqual(strip_accents("\u0301"), "")


if __name__ == "__main__":
    unittest.main()
