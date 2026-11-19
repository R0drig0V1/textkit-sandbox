"""Tests for textkit.strings, one TestCase class per public function."""

import unicodedata
import unittest

from textkit.strings import slugify, squeeze, strip_accents, truncate, wrap


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


class SlugifyTest(unittest.TestCase):
    def test_basic_example(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_lower_cases(self):
        self.assertEqual(slugify("ABC Def"), "abc-def")

    def test_run_of_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  --  b...c"), "a-b-c")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case__name"), "snake-case-name")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--  hello  --"), "hello")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Version 2.0"), "version-2-0")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input(self):
        text = unicodedata.normalize("NFC", "Ñandú")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input(self):
        text = unicodedata.normalize("NFD", "Ñandú")
        self.assertEqual(slugify(text), "nandu")

    def test_non_ascii_that_lowercases_to_ascii_is_removed(self):
        # KELVIN SIGN lower-cases to ASCII "k"; it must be removed before lower-casing.
        self.assertEqual(slugify("K"), "")
        self.assertEqual(slugify("İstanbul"), "stanbul")

    def test_non_ascii_alphanumerics_are_not_kept(self):
        self.assertEqual(slugify("a²b ٣"), "ab")

    def test_empty(self):
        self.assertEqual(slugify(""), "")

    def test_punctuation_only(self):
        self.assertEqual(slugify("!!!"), "")


class WrapTest(unittest.TestCase):
    def test_fills_lines_greedily_at_spaces(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_can_be_exactly_width(self):
        self.assertEqual(wrap("ab cd ef", 5), ["ab cd", "ef"])

    def test_text_that_fits_is_one_line(self):
        self.assertEqual(wrap("hello world", 11), ["hello world"])

    def test_every_line_is_at_most_width(self):
        text = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do"
        for width in range(11, 30):
            lines = wrap(text, width)
            self.assertTrue(all(len(line) <= width for line in lines), (width, lines))
            self.assertEqual(" ".join(lines), text)

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(wrap("a supercalifragilistic b", 5), ["a", "supercalifragilistic", "b"])

    def test_long_word_first_and_last(self):
        self.assertEqual(wrap("abcdefgh ij", 3), ["abcdefgh", "ij"])
        self.assertEqual(wrap("ij abcdefgh", 3), ["ij", "abcdefgh"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b     c", 80), ["a b c"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 80), ["a b"])

    def test_lines_never_contain_the_separating_space(self):
        for line in wrap("aa  bb   cc dd", 5):
            self.assertFalse(line.startswith(" ") or line.endswith(" "), line)

    def test_empty_text_gives_no_lines(self):
        self.assertEqual(wrap("", 5), [])

    def test_only_spaces_or_newlines_gives_no_lines(self):
        self.assertEqual(wrap("     ", 5), [])
        self.assertEqual(wrap("\n\n \r\n", 5), [])

    def test_width_below_one_raises(self):
        with self.assertRaises(ValueError):
            wrap("hello", 0)
        with self.assertRaises(ValueError):
            wrap("hello", -3)
        with self.assertRaises(ValueError):
            wrap("", 0)

    def test_width_one(self):
        self.assertEqual(wrap("a b cd", 1), ["a", "b", "cd"])

    # ADR "`wrap` reflows text": existing line breaks separate words like a space.
    def test_newlines_are_word_separators(self):
        self.assertEqual(wrap("one\ntwo three", 80), ["one two three"])

    def test_blank_lines_are_not_kept(self):
        self.assertEqual(wrap("one\n\ntwo", 80), ["one two"])

    def test_newline_mixed_with_spaces_collapses(self):
        self.assertEqual(wrap("one \n  two", 80), ["one two"])

    def test_other_line_breaks_are_separators(self):
        self.assertEqual(wrap("a\r\nb\rc\u2028d", 80), ["a b c d"])

    def test_newlines_reflow_with_width(self):
        self.assertEqual(wrap("aa bb\ncc dd", 5), ["aa bb", "cc dd"])
        self.assertEqual(wrap("aa\nbb cc", 5), ["aa bb", "cc"])

    def test_no_line_contains_a_line_break(self):
        for line in wrap("a\nb\r\nc d\n", 3):
            self.assertEqual(line.splitlines(), [line])

    def test_tabs_and_no_break_spaces_are_part_of_words(self):
        self.assertEqual(wrap("a\tb c", 3), ["a\tb", "c"])
        self.assertEqual(wrap("a\u00a0b c", 3), ["a\u00a0b", "c"])


if __name__ == "__main__":
    unittest.main()
