import unicodedata
import unittest

from textkit.strings import slug_title, slugify, squeeze, strip_accents, truncate, wrap


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("na\u00efve"), "nave")

    def test_nfc_input(self):
        # "Ñandú" as typed (precomposed): Ñ and ú are non-ASCII and vanish.
        self.assertEqual(slugify("\u00d1and\u00fa"), "and")

    def test_nfd_input(self):
        # Decomposed: only the combining marks are non-ASCII, the base letters stay.
        self.assertEqual(slugify("N\u0303andu\u0301"), "nandu")

    def test_empty_and_punctuation_only(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case__name"), "snake-case-name")

    def test_runs_collapse_and_ends_stripped(self):
        self.assertEqual(slugify("  --Foo   Bar 42!! "), "foo-bar-42")

    def test_non_ascii_digits_and_letters_removed(self):
        # Arabic-Indic digit, superscript two and the Kelvin sign are non-ASCII.
        self.assertEqual(slugify("a\u0661b\u00b2c\u212a"), "abc")


class StripAccentsTest(unittest.TestCase):
    def test_removes_accents_from_nfc_input(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_removes_accents_from_nfd_input(self):
        self.assertEqual(strip_accents(unicodedata.normalize("NFD", "Ñandú")), "Nandu")

    def test_several_marks_on_one_letter(self):
        self.assertEqual(strip_accents("ệ"), "e")

    def test_plain_ascii_unchanged(self):
        self.assertEqual(strip_accents("Hello, World!"), "Hello, World!")

    def test_empty_string(self):
        self.assertEqual(strip_accents(""), "")

    def test_letters_without_decomposition_are_kept(self):
        self.assertEqual(strip_accents("øłß"), "øłß")

    def test_non_latin_text_is_recomposed(self):
        self.assertEqual(strip_accents("한국어"), "한국어")


class TruncateTest(unittest.TestCase):
    def test_returns_text_unchanged_when_shorter(self):
        self.assertEqual(truncate("hello", 10), "hello")

    def test_returns_text_unchanged_when_exactly_width(self):
        self.assertEqual(truncate("hello", 5), "hello")

    def test_cuts_to_exact_width_with_default_suffix(self):
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_keeps_start_of_text(self):
        self.assertEqual(truncate("abcdefghij", 6), "abc...")

    def test_custom_suffix(self):
        self.assertEqual(truncate("hello world", 7, suffix="~"), "hello ~")

    def test_empty_suffix_is_plain_cut(self):
        self.assertEqual(truncate("hello world", 5, suffix=""), "hello")

    def test_width_equal_to_suffix_gives_only_suffix(self):
        self.assertEqual(truncate("hello world", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("x", 0, suffix=""), "")

    def test_empty_text_fits(self):
        self.assertEqual(truncate("", 3), "")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("hello world", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("hi", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_with_empty_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("", -1, suffix="")

    def test_counts_code_points(self):
        self.assertEqual(truncate("ñandú y más", 7), "ñand...")
        self.assertEqual(truncate("ñandú", 5), "ñandú")


class WrapTest(unittest.TestCase):
    def test_greedy_packing(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("ab cd ef", 5), ["ab cd", "ef"])

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(wrap("a abcdefgh b", 3), ["a", "abcdefgh", "b"])

    def test_long_word_alone(self):
        self.assertEqual(wrap("abcdefgh", 3), ["abcdefgh"])

    def test_runs_of_spaces_collapse_and_ends_dropped(self):
        self.assertEqual(wrap("   a    b   ", 10), ["a b"])

    def test_lines_never_contain_the_separating_space(self):
        for line in wrap("aa bb cc dd ee", 5):
            self.assertFalse(line.startswith(" ") or line.endswith(" "), line)

    def test_newlines_and_tabs_are_spaces(self):
        # ADR 0003: existing newlines do not force a break; the text is reflowed.
        self.assertEqual(wrap("one\ntwo\n\nthree\tfour", 9), ["one two", "three", "four"])
        self.assertEqual(wrap("a\nb", 10), ["a b"])

    def test_empty_and_blank(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("  \n\t ", 5), [])

    def test_width_one(self):
        self.assertEqual(wrap("a b", 1), ["a", "b"])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("a b", width)
        with self.assertRaises(ValueError):
            wrap("", 0)


class SlugTitleTest(unittest.TestCase):
    def test_character_cut_inside_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_trailing_dash_stripped(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_fits_unchanged(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")

    def test_zero_gives_empty(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_never_longer_than_max_len(self):
        for n in range(0, 15):
            result = slug_title("Hello, World!", n)
            self.assertLessEqual(len(result), n)
            self.assertFalse(result.endswith("-"))

    def test_empty_slug(self):
        self.assertEqual(slug_title("!!!", 5), "")

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("Hello", -1)


if __name__ == "__main__":
    unittest.main()
