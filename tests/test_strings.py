"""Tests for textkit.strings."""

import unicodedata
import unittest

from textkit.strings import slug_title, slugify, squeeze, strip_accents, truncate, wrap


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


class WrapTest(unittest.TestCase):
    """One test per rule of ADR 0003, plus the basic behaviour of the plan task."""

    def test_greedy_split_at_spaces(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_of_exactly_width_fits(self):
        self.assertEqual(wrap("ab cd ef", 5), ["ab cd", "ef"])
        self.assertEqual(wrap("abcde", 5), ["abcde"])

    def test_text_that_fits_is_one_line(self):
        self.assertEqual(wrap("hello world", 80), ["hello world"])

    def test_no_line_exceeds_width_unless_it_is_one_long_word(self):
        text = "a bb ccc dddd eeeee ffffff ggggggg hhhhhhhh"
        for width in range(1, 12):
            for line in wrap(text, width):
                self.assertTrue(len(line) <= width or " " not in line, (width, line))

    def test_long_word_gets_its_own_line_unbroken(self):
        self.assertEqual(wrap("a supercalifragilistic b", 5), ["a", "supercalifragilistic", "b"])
        self.assertEqual(wrap("toolongword", 3), ["toolongword"])

    def test_width_one_puts_each_word_on_its_own_line(self):
        self.assertEqual(wrap("a b cc", 1), ["a", "b", "cc"])

    # Rule 1: existing line breaks are hard breaks.
    def test_newline_is_a_hard_break(self):
        self.assertEqual(wrap("a b\nc d", 80), ["a b", "c d"])

    def test_each_source_line_is_wrapped_on_its_own(self):
        self.assertEqual(wrap("aaa bbb\nccc", 7), ["aaa bbb", "ccc"])
        self.assertEqual(wrap("aaa bbb ccc\nd", 7), ["aaa bbb", "ccc", "d"])

    def test_crlf_is_one_break_and_cr_is_a_break(self):
        self.assertEqual(wrap("a\r\nb", 80), ["a", "b"])
        self.assertEqual(wrap("a\rb", 80), ["a", "b"])

    def test_other_splitlines_boundaries_are_breaks(self):
        for sep in ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"]:
            self.assertEqual(wrap("a" + sep + "b", 80), ["a", "b"], repr(sep))

    # Rule 2: a final line break adds nothing.
    def test_trailing_newline_adds_no_empty_line(self):
        self.assertEqual(wrap("a\n", 80), ["a"])
        self.assertEqual(wrap("a\r\n", 80), ["a"])

    # Rule 3: a source line with no words gives exactly one empty string.
    def test_blank_line_is_kept_as_empty_string(self):
        self.assertEqual(wrap("a\n\nb", 80), ["a", "", "b"])

    def test_consecutive_blank_lines_are_each_kept(self):
        self.assertEqual(wrap("a\n\n\nb", 80), ["a", "", "", "b"])

    def test_whitespace_only_line_is_an_empty_string(self):
        self.assertEqual(wrap("a\n \t \nb", 80), ["a", "", "b"])

    def test_leading_newline_gives_leading_empty_string(self):
        self.assertEqual(wrap("\na", 80), ["", "a"])
        self.assertEqual(wrap("\n", 80), [""])

    def test_join_keeps_paragraph_layout(self):
        text = "first paragraph here\n\nsecond one"
        self.assertEqual("\n".join(wrap(text, 80)), text)

    # Rule 4: inside a line, any run of whitespace is one separator.
    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b", 80), ["a b"])

    def test_runs_of_spaces_do_not_count_towards_width(self):
        self.assertEqual(wrap("ab      cd", 5), ["ab cd"])

    def test_leading_and_trailing_whitespace_is_dropped(self):
        self.assertEqual(wrap("  a b  ", 80), ["a b"])
        self.assertEqual(wrap("  a\n  b  ", 80), ["a", "b"])

    def test_tabs_separate_words_and_are_not_expanded(self):
        self.assertEqual(wrap("a\tb", 80), ["a b"])
        self.assertEqual(wrap("a\t\tb", 3), ["a b"])
        self.assertEqual(wrap("\ta", 80), ["a"])

    def test_other_unicode_whitespace_separates_words(self):
        self.assertEqual(wrap("a\u00a0b\u3000c", 80), ["a b c"])

    # Rule 5: width is measured in code points.
    def test_width_counts_code_points(self):
        self.assertEqual(wrap("ñandú café", 5), ["ñandú", "café"])
        self.assertEqual(wrap("日本 語", 4), ["日本 語"])

    # Rule 7: empty text and whitespace-only text.
    def test_empty_text_gives_empty_list(self):
        self.assertEqual(wrap("", 10), [])

    def test_whitespace_only_text_gives_one_empty_string(self):
        self.assertEqual(wrap("   ", 10), [""])
        self.assertEqual(wrap("\t", 10), [""])

    # Rule 8: width <= 0 raises ValueError, checked first.
    def test_zero_or_negative_width_raises(self):
        for width in (0, -1, -100):
            with self.assertRaises(ValueError):
                wrap("a b", width)

    def test_width_is_checked_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            wrap("", 0)

    def test_returns_a_list_of_str(self):
        result = wrap("a b", 1)
        self.assertIsInstance(result, list)
        self.assertTrue(all(isinstance(line, str) for line in result))


class SlugTitleTest(unittest.TestCase):
    def assertWellFormed(self, result, max_len):
        self.assertLessEqual(len(result), max_len)
        self.assertFalse(result.startswith("-"), result)
        self.assertFalse(result.endswith("-"), result)
        self.assertNotIn("--", result)

    def test_slug_that_fits_is_unchanged(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")
        self.assertEqual(slug_title("Hello, World!", 50), "hello-world")

    def test_cuts_at_a_word_boundary(self):
        # Cuts that land inside "world" drop the partial word.
        self.assertEqual(slug_title("Hello big world", 12), "hello-big")
        self.assertEqual(slug_title("Hello big world", 14), "hello-big")

    def test_cut_landing_right_before_a_dash(self):
        # slug[9] is "-": the first 9 characters are whole words already.
        self.assertEqual(slug_title("Hello big world", 9), "hello-big")

    def test_cut_landing_right_after_a_dash_drops_it(self):
        # "hello-big-" is the first 10 characters; the trailing "-" goes.
        self.assertEqual(slug_title("Hello big world", 10), "hello-big")
        self.assertEqual(slug_title("a b c", 2), "a")

    def test_first_word_longer_than_max_len_is_cut_mid_word(self):
        self.assertEqual(slug_title("Internationalization", 5), "inter")
        self.assertEqual(slug_title("Internationalization rocks", 5), "inter")

    def test_empty_slug_gives_empty_string(self):
        self.assertEqual(slug_title("", 10), "")
        self.assertEqual(slug_title("!?", 10), "")
        self.assertEqual(slug_title("日本語", 10), "")
        self.assertEqual(slug_title("!?", 0), "")

    def test_max_len_zero_gives_empty_string(self):
        self.assertEqual(slug_title("Hello", 0), "")

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("Hello", -1)

    def test_negative_max_len_raises_even_for_an_empty_slug(self):
        with self.assertRaises(ValueError):
            slug_title("", -1)

    def test_result_is_always_well_formed(self):
        texts = ["", "!?", "a", "Hello big world", "  --Top 10--  ", "a b c d e",
                 "Internationalization rocks", "x-y_z w", "v1.2.3 release notes"]
        for text in texts:
            slug = slugify(text)
            for max_len in range(len(slug) + 2):
                with self.subTest(text=text, max_len=max_len):
                    result = slug_title(text, max_len)
                    self.assertWellFormed(result, max_len)
                    self.assertTrue(slug.startswith(result))


if __name__ == "__main__":
    unittest.main()
