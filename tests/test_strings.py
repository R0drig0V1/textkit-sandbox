import unicodedata
import unittest

from textkit.strings import is_palindrome, slug_title, slugify, squeeze, strip_accents, truncate, wrap


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


class StripAccentsTest(unittest.TestCase):
    def test_removes_accents_from_nfc_input(self):
        self.assertEqual(strip_accents("\u00d1and\u00fa"), "Nandu")

    def test_removes_accents_from_nfd_input(self):
        nfd = unicodedata.normalize("NFD", "\u00d1and\u00fa")
        self.assertNotEqual(nfd, "\u00d1and\u00fa")
        self.assertEqual(strip_accents(nfd), "Nandu")

    def test_sentence(self):
        self.assertEqual(strip_accents("Cr\u00e8me br\u00fbl\u00e9e"), "Creme brulee")

    def test_letters_without_decomposition_are_kept(self):
        for letter in ("\u00f8", "\u00d8", "\u00df", "\u0142", "\u0111", "\u00e6"):
            with self.subTest(letter=letter):
                self.assertEqual(strip_accents(letter), letter)
        self.assertEqual(strip_accents("stra\u00dfe"), "stra\u00dfe")

    def test_mixed_letters(self):
        self.assertEqual(strip_accents("S\u00f8ren \u00c5ngstr\u00f6m"), "S\u00f8ren Angstrom")

    def test_compatibility_characters_are_kept(self):
        self.assertEqual(strip_accents("\ufb01"), "\ufb01")

    def test_multiple_marks_on_one_letter(self):
        self.assertEqual(strip_accents("\u1ec7"), "e")
        self.assertEqual(strip_accents("a\u0301\u0308"), "a")

    def test_only_nonzero_combining_class_is_removed(self):
        self.assertEqual(strip_accents("\u0915\u094d"), "\u0915")
        self.assertEqual(strip_accents("\u0915\u093f"), "\u0915\u093f")
        self.assertEqual(strip_accents("a\u20dd"), "a\u20dd")

    def test_lone_combining_mark(self):
        self.assertEqual(strip_accents("\u0301"), "")

    def test_result_is_nfc(self):
        self.assertEqual(strip_accents("\ud55c\uad6d\uc5b4"), "\ud55c\uad6d\uc5b4")

    def test_plain_ascii_and_empty_unchanged(self):
        self.assertEqual(strip_accents("Hello, World! 123"), "Hello, World! 123")
        self.assertEqual(strip_accents(""), "")


class WrapTest(unittest.TestCase):
    def test_fills_lines_greedily(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("ab cd ef", 5), ["ab cd", "ef"])

    def test_everything_fits_on_one_line(self):
        self.assertEqual(wrap("hello world", 80), ["hello world"])

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(wrap("a abcdefgh b", 3), ["a", "abcdefgh", "b"])
        self.assertEqual(wrap("abcdefgh", 3), ["abcdefgh"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b     c", 80), ["a b c"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 80), ["a b"])

    def test_lines_never_contain_the_separating_space(self):
        for line in wrap("  aa   bb  cc dd   ee  ", 5):
            self.assertEqual(line, line.strip())
            self.assertLessEqual(len(line), 5)

    def test_empty_and_whitespace_only(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("   ", 5), [])
        self.assertEqual(wrap(" \t\n\r\n ", 5), [])

    def test_width_below_one_raises(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("a b", width)
        with self.assertRaises(ValueError):
            wrap("", 0)

    def test_width_one(self):
        self.assertEqual(wrap("a b cd", 1), ["a", "b", "cd"])

    # ADR 0003: existing newlines (and other whitespace) are separators; text is reflowed.
    def test_newlines_are_reflowed_like_spaces(self):
        self.assertEqual(wrap("one\ntwo\nthree", 80), ["one two three"])
        self.assertEqual(wrap("para one\n\npara two", 80), ["para one para two"])
        self.assertEqual(wrap("a\r\nb", 80), ["a b"])

    def test_newline_does_not_force_a_break(self):
        self.assertEqual(wrap("ab\ncd ef", 5), ["ab cd", "ef"])

    def test_tabs_and_other_whitespace_are_separators(self):
        self.assertEqual(wrap("a\tb\fc\vd", 80), ["a b c d"])
        self.assertEqual(wrap("a\u2003b\u2028c\u3000d", 80), ["a b c d"])

    def test_non_breaking_spaces_stay_inside_words(self):
        for nbsp in ("\u00a0", "\u2007", "\u202f"):
            word = "10" + nbsp + "km"
            self.assertEqual(wrap("run " + word + " today", 6), ["run", word, "today"])


class SlugTitleTest(unittest.TestCase):
    # The four examples pinned by T1.9 in docs/phases/phase-1-core-helpers.md.
    def test_cut_inside_a_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_trailing_dash_after_cut_is_stripped(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_exact_fit_unchanged(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")

    def test_zero_length(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_longer_than_slug_unchanged(self):
        self.assertEqual(slug_title("Hello, World!", 50), "hello-world")

    def test_nothing_left_after_slugify(self):
        self.assertEqual(slug_title("!!!", 5), "")
        self.assertEqual(slug_title("", 0), "")

    def test_never_ends_in_dash_and_respects_max_len(self):
        text = "  A quick -- brown_fox, 2.0!  "
        for max_len in range(0, 30):
            with self.subTest(max_len=max_len):
                result = slug_title(text, max_len)
                self.assertLessEqual(len(result), max_len)
                self.assertFalse(result.endswith("-"))
                self.assertEqual(result, truncate(slugify(text), max_len, suffix="").rstrip("-"))

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("Hello", -1)
        with self.assertRaises(ValueError):
            slug_title("", -1)


class IsPalindromeTest(unittest.TestCase):
    def test_simple_words(self):
        self.assertTrue(is_palindrome("racecar"))
        self.assertFalse(is_palindrome("hello"))

    def test_ignores_case(self):
        self.assertTrue(is_palindrome("RaceCar"))

    def test_ignores_spaces_and_punctuation(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama!"))
        self.assertTrue(is_palindrome("Was it a car or a cat I saw?"))
        self.assertFalse(is_palindrome("A man, a plan, a canal: Suez!"))

    def test_underscore_and_symbols_are_ignored(self):
        self.assertTrue(is_palindrome("a_b-a"))
        self.assertTrue(is_palindrome("ab\u20acba"))

    def test_ignores_accents_nfc_and_nfd(self):
        self.assertTrue(is_palindrome("\u00c1n\u00e0"))
        self.assertTrue(is_palindrome(unicodedata.normalize("NFD", "\u00c1n\u00e0")))
        self.assertTrue(is_palindrome("S\u00e9 es"))

    def test_letters_without_decomposition_stay_distinct(self):
        self.assertTrue(is_palindrome("\u00f8\u00d8"))
        self.assertFalse(is_palindrome("\u00f8o"))

    def test_casefold_not_lower(self):
        # "\u00df".lower() is "\u00df" but casefold() is "ss": "s\u00df" -> "sss".
        self.assertTrue(is_palindrome("s\u00df"))
        self.assertTrue(is_palindrome("\u0130i"))

    def test_digits_count(self):
        self.assertTrue(is_palindrome("12321"))
        self.assertFalse(is_palindrome("123"))
        self.assertTrue(is_palindrome("a1a"))
        self.assertFalse(is_palindrome("1a2"))

    def test_non_latin_letters(self):
        self.assertTrue(is_palindrome("\u0410\u0431\u0431\u0430"))
        self.assertFalse(is_palindrome("\u0410\u0431\u0432"))

    def test_empty_and_no_alphanumerics_are_true(self):
        for text in ("", "   ", "!!!", ".,;-", "\u0301"):
            with self.subTest(text=text):
                self.assertTrue(is_palindrome(text))

    def test_single_character(self):
        self.assertTrue(is_palindrome("x"))
        self.assertTrue(is_palindrome("7"))


if __name__ == "__main__":
    unittest.main()
