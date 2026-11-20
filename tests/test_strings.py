import unittest

import unicodedata

from textkit.strings import slugify, squeeze, strip_accents, truncate, wrap


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


class WrapTest(unittest.TestCase):
    def test_greedy_fill(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("ab cd", 5), ["ab cd"])
        self.assertEqual(wrap("ab cd", 4), ["ab", "cd"])

    def test_long_word_gets_own_line(self):
        self.assertEqual(wrap("a abcdefgh b", 3), ["a", "abcdefgh", "b"])

    def test_long_word_is_not_split(self):
        self.assertEqual(wrap("abcdefgh", 3), ["abcdefgh"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a     b", 10), ["a b"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 10), ["a b"])

    def test_lines_never_contain_separating_space(self):
        for line in wrap("aa  bb   cc dd ee", 5):
            self.assertFalse(line.startswith(" ") or line.endswith(" "), line)

    def test_empty_and_whitespace_only(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("     ", 5), [])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("abc", width)
        with self.assertRaises(ValueError):
            wrap("", 0)

    def test_width_one(self):
        self.assertEqual(wrap("a b cd", 1), ["a", "b", "cd"])

    # ADR 0003: existing newlines are separators, like spaces.
    def test_newlines_are_separators(self):
        self.assertEqual(wrap("a\nb", 10), ["a b"])

    def test_paragraph_breaks_are_not_kept(self):
        self.assertEqual(wrap("one two\n\nthree", 7), ["one two", "three"])

    def test_crlf_tabs_and_unicode_line_separators(self):
        self.assertEqual(wrap("a\r\nb\tc\u2028d", 20), ["a b c d"])

    def test_no_line_contains_a_newline(self):
        for line in wrap("x\ny\n\nz w\n", 3):
            self.assertNotIn("\n", line)


if __name__ == "__main__":
    unittest.main()
