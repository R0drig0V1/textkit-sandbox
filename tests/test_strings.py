import unicodedata
import unittest

from textkit.strings import slug_title, slugify, squeeze, strip_accents, truncate, wrap


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


class SlugTitleTest(unittest.TestCase):
    def test_cut_inside_a_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_cut_after_separator_strips_trailing_hyphen(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_fits_is_full_slug(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")

    def test_zero_max_len_gives_empty(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_matches_truncate_of_slugify(self):
        for n in range(0, 15):
            expected = truncate(slugify("Hello, World!"), n, suffix="").rstrip("-")
            self.assertEqual(slug_title("Hello, World!", n), expected)
            self.assertLessEqual(len(slug_title("Hello, World!", n)), n)

    def test_empty_slug_gives_empty(self):
        self.assertEqual(slug_title("!!!", 5), "")

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("Hello", -1)


class StripAccentsTest(unittest.TestCase):
    def test_removes_accents_nfc(self):
        self.assertEqual(strip_accents("\u00d1and\u00fa"), "Nandu")

    def test_removes_accents_nfd(self):
        self.assertEqual(strip_accents("N\u0303andu\u0301"), "Nandu")

    def test_several_marks_on_one_letter(self):
        self.assertEqual(strip_accents("\u1ec7"), "e")  # e with circumflex and dot below

    def test_plain_ascii_unchanged(self):
        self.assertEqual(strip_accents("Hello, World!"), "Hello, World!")

    def test_empty(self):
        self.assertEqual(strip_accents(""), "")

    def test_letters_without_decomposition_kept(self):
        self.assertEqual(strip_accents("\u00f8\u0142\u00df"), "\u00f8\u0142\u00df")

    def test_non_latin_recomposed(self):
        self.assertEqual(strip_accents("\ud55c\uae00"), "\ud55c\uae00")  # Hangul


class WrapTest(unittest.TestCase):
    def test_fills_lines_greedily(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("ab cd", 5), ["ab cd"])
        self.assertEqual(wrap("ab cd", 4), ["ab", "cd"])

    def test_every_line_fits_and_has_no_edge_space(self):
        lines = wrap("lorem ipsum dolor sit amet consectetur adipiscing elit", 12)
        for line in lines:
            self.assertLessEqual(len(line), 12)
            self.assertEqual(line, line.strip())

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(wrap("a extraordinary b", 5), ["a", "extraordinary", "b"])

    def test_long_word_alone(self):
        self.assertEqual(wrap("extraordinary", 3), ["extraordinary"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b", 10), ["a b"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 10), ["a b"])

    def test_separating_space_is_not_kept(self):
        self.assertEqual(wrap("aaa bbb", 3), ["aaa", "bbb"])
        self.assertEqual(wrap("aaa   bbb", 4), ["aaa", "bbb"])

    def test_empty_text_gives_no_lines(self):
        self.assertEqual(wrap("", 5), [])

    def test_whitespace_only_gives_no_lines(self):
        self.assertEqual(wrap("   \n  ", 5), [])

    def test_newlines_are_separators_and_text_is_reflowed(self):
        # ADR 0003: existing newlines are not kept as line breaks.
        self.assertEqual(wrap("one\ntwo three", 20), ["one two three"])
        self.assertEqual(wrap("a\n\nb", 20), ["a b"])
        self.assertEqual(wrap("a\r\nb\tc", 20), ["a b c"])

    def test_no_line_contains_a_newline(self):
        for line in wrap("alpha\nbeta\ngamma delta", 6):
            self.assertNotIn("\n", line)

    def test_width_one(self):
        self.assertEqual(wrap("a b c", 1), ["a", "b", "c"])

    def test_counts_code_points(self):
        self.assertEqual(wrap("ñandú ñu", 8), ["ñandú ñu"])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("a b", width)

    def test_width_below_one_raises_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            wrap("", 0)


if __name__ == "__main__":
    unittest.main()
