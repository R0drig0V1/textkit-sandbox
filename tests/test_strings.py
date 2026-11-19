import unittest

from textkit.strings import squeeze, truncate


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


if __name__ == "__main__":
    unittest.main()
