import unittest

import unicodedata

from textkit.strings import slugify, squeeze, truncate, wrap


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_joins_words(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_removes_non_ascii_without_separator(self):
        self.assertEqual(slugify("na\u00efve"), "nave")

    def test_nfc_input_drops_precomposed_letters(self):
        text = unicodedata.normalize("NFC", "\u00d1and\u00fa")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input_keeps_base_letters(self):
        text = unicodedata.normalize("NFD", "\u00d1and\u00fa")
        self.assertEqual(slugify(text), "nandu")

    def test_underscore_and_runs_become_one_hyphen(self):
        self.assertEqual(slugify("a__b --  c"), "a-b-c")

    def test_strips_hyphens_at_both_ends(self):
        self.assertEqual(slugify("--Hi--"), "hi")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Route 66"), "route-66")

    def test_non_ascii_that_lowercases_to_ascii_is_removed(self):
        # KELVIN SIGN lower-cases to "k"; it must be removed, not kept.
        self.assertEqual(slugify("\u212a9"), "9")

    def test_empty_and_punctuation_only_give_empty(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")


class WrapTest(unittest.TestCase):
    def test_greedy_packing(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_exact_fit(self):
        self.assertEqual(wrap("ab cd", 5), ["ab cd"])
        self.assertEqual(wrap("ab cd", 4), ["ab", "cd"])

    def test_long_word_gets_own_line(self):
        self.assertEqual(wrap("a abcdefgh b", 3), ["a", "abcdefgh", "b"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b", 10), ["a b"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 10), ["a b"])

    def test_lines_never_contain_separating_space(self):
        for line in wrap("aa bb cc dd ee", 5):
            self.assertFalse(line.startswith(" ") or line.endswith(" "))
            self.assertLessEqual(len(line), 5)

    def test_empty_and_blank_input(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("   ", 5), [])
        self.assertEqual(wrap(" \n \r\n ", 5), [])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("a", width)

    def test_width_one(self):
        self.assertEqual(wrap("a b", 1), ["a", "b"])

    def test_newlines_are_reflowed_like_spaces(self):
        # ADR 0001: existing line breaks are separators, not hard breaks.
        self.assertEqual(wrap("one\ntwo three", 20), ["one two three"])
        self.assertEqual(wrap("a\r\nb\rc", 10), ["a b c"])
        self.assertEqual(wrap("a\n\nb", 10), ["a b"])

    def test_tabs_stay_inside_words(self):
        self.assertEqual(wrap("a\tb c", 3), ["a\tb", "c"])

    def test_width_counts_code_points(self):
        self.assertEqual(wrap("ñandú ñu", 8), ["ñandú ñu"])


class TruncateTest(unittest.TestCase):
    def test_returns_text_unchanged_when_shorter_than_width(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_returns_text_unchanged_when_exactly_width(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cuts_to_exact_width_with_default_suffix(self):
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 6, suffix="~"), "hello~")

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_length_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_zero_width_with_empty_suffix(self):
        self.assertEqual(truncate("hello", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_counts_code_points(self):
        # Five code points (NFC input) fit in width 5; six do not.
        self.assertEqual(truncate("ñandú", 5), "ñandú")
        self.assertEqual(truncate("ñandú!", 5, suffix="."), "ñand.")

    def test_width_smaller_than_suffix_raises_when_text_is_long(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_when_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("hi", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")


if __name__ == "__main__":
    unittest.main()
