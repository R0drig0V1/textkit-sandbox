import unicodedata
import unittest

from textkit.strings import squeeze, truncate
from textkit.strings import strip_accents
from textkit.strings import slugify
from textkit.strings import wrap
from textkit.strings import slug_title
from textkit.strings import is_palindrome


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


class SlugifyTest(unittest.TestCase):
    def test_basic_example(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_run_of_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  --  b...c"), "a-b-c")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--  Hello  --"), "hello")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Python 3.9 Release"), "python-3-9-release")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("na\u00efve"), "nave")

    def test_nfc_input(self):
        # "Nandu" with tilde and acute as typed (NFC): two single non-ASCII code points,
        # both removed with no separator.
        text = unicodedata.normalize("NFC", "\u00d1and\u00fa")
        self.assertEqual(len(text), 5)
        self.assertEqual(slugify(text), "and")

    def test_nfd_input(self):
        # The same word in NFD: ASCII base letters plus combining marks; only the marks go.
        text = unicodedata.normalize("NFD", "\u00d1and\u00fa")
        self.assertEqual(len(text), 7)
        self.assertEqual(slugify(text), "nandu")

    def test_non_ascii_digits_are_removed(self):
        # ARABIC-INDIC DIGIT THREE passes str.isalnum but is not ASCII.
        self.assertEqual(slugify("a\u0663b"), "ab")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_punctuation_only(self):
        self.assertEqual(slugify("!!!"), "")


class WrapTest(unittest.TestCase):
    def test_packs_words_greedily_at_spaces(self):
        self.assertEqual(
            wrap("the quick brown fox jumps", 10), ["the quick", "brown fox", "jumps"]
        )

    def test_line_may_be_exactly_width(self):
        self.assertEqual(wrap("abc def", 7), ["abc def"])
        self.assertEqual(wrap("abc def", 6), ["abc", "def"])

    def test_lines_never_exceed_width_or_contain_edge_spaces(self):
        for line in wrap("lorem ipsum dolor sit amet consectetur adipiscing elit", 12):
            self.assertLessEqual(len(line), 12)
            self.assertEqual(line, line.strip(" "))

    def test_long_word_gets_its_own_line(self):
        self.assertEqual(wrap("a extraordinary b", 5), ["a", "extraordinary", "b"])
        self.assertEqual(wrap("extraordinary", 5), ["extraordinary"])

    def test_runs_of_spaces_collapse(self):
        self.assertEqual(wrap("a    b     c", 80), ["a b c"])

    def test_leading_and_trailing_spaces_dropped(self):
        self.assertEqual(wrap("   a b   ", 80), ["a b"])

    def test_empty_and_blank_text_give_no_lines(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("     ", 5), [])

    def test_width_one(self):
        self.assertEqual(wrap("a b cd", 1), ["a", "b", "cd"])

    def test_width_below_one_raises(self):
        with self.assertRaises(ValueError):
            wrap("abc", 0)
        with self.assertRaises(ValueError):
            wrap("abc", -3)
        with self.assertRaises(ValueError):
            wrap("", 0)

    def test_newlines_are_treated_as_spaces(self):
        # ADR 0003: existing line breaks are reflowed, never kept.
        self.assertEqual(wrap("one\ntwo three", 80), ["one two three"])
        self.assertEqual(wrap("one\r\ntwo\rthree", 80), ["one two three"])
        self.assertEqual(wrap("one\n\ntwo", 80), ["one two"])
        self.assertEqual(wrap("\nab cd\n", 2), ["ab", "cd"])
        self.assertEqual(wrap("\n\n", 5), [])

    def test_other_whitespace_is_not_a_break_point(self):
        self.assertEqual(wrap("a\tb c", 3), ["a\tb", "c"])
        self.assertEqual(wrap("a\u00a0b c", 3), ["a\u00a0b", "c"])

    def test_counts_code_points(self):
        self.assertEqual(wrap("ñandú ñu", 8), ["ñandú ñu"])


class SlugTitleTest(unittest.TestCase):
    def test_cut_inside_a_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_trailing_dash_after_cut_is_stripped(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_slug_that_fits_is_unchanged(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")

    def test_zero_length_gives_empty(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_max_len_larger_than_slug(self):
        self.assertEqual(slug_title("Hello, World!", 100), "hello-world")

    def test_input_with_no_slug_characters_gives_empty(self):
        self.assertEqual(slug_title("!!!", 5), "")

    def test_never_ends_in_dash(self):
        text = "a-b c_d e.f"
        for max_len in range(len(text) + 2):
            with self.subTest(max_len=max_len):
                result = slug_title(text, max_len)
                self.assertLessEqual(len(result), max_len)
                self.assertFalse(result.endswith("-"))
                self.assertEqual(result, truncate(slugify(text), max_len, suffix="").rstrip("-"))

    def test_negative_max_len_raises(self):
        with self.assertRaises(ValueError):
            slug_title("Hello", -1)

    def test_negative_max_len_raises_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            slug_title("", -1)


class IsPalindromeTest(unittest.TestCase):
    def test_simple_palindromes(self):
        self.assertTrue(is_palindrome("radar"))
        self.assertTrue(is_palindrome("a"))
        self.assertTrue(is_palindrome("abba"))

    def test_not_palindromes(self):
        self.assertFalse(is_palindrome("hello"))
        self.assertFalse(is_palindrome("ab"))
        self.assertFalse(is_palindrome("12a3"))

    def test_ignores_case_spaces_and_punctuation(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama!"))
        self.assertTrue(is_palindrome("Was it a car or a cat I saw?"))

    def test_ignores_accents(self):
        self.assertTrue(is_palindrome("Dábale arroz a la zorra el abad"))
        self.assertTrue(is_palindrome("Ána"))

    def test_nfc_and_nfd_input_give_the_same_result(self):
        for form in ("NFC", "NFD"):
            with self.subTest(form=form):
                text = unicodedata.normalize(form, "Átá")
                self.assertTrue(is_palindrome(text))

    def test_digits_count(self):
        self.assertTrue(is_palindrome("12321"))
        self.assertTrue(is_palindrome("1a1"))
        self.assertFalse(is_palindrome("123"))

    def test_casefold_not_lower(self):
        # casefold maps "ß" to "ss", lower() does not.
        self.assertTrue(is_palindrome("ßs"))

    def test_empty_and_no_alphanumerics_return_true(self):
        self.assertTrue(is_palindrome(""))
        self.assertTrue(is_palindrome("   "))
        self.assertTrue(is_palindrome("!?., -"))

    def test_letters_of_other_scripts(self):
        self.assertTrue(is_palindrome("άνά"))
        self.assertFalse(is_palindrome("αβ"))


if __name__ == "__main__":
    unittest.main()
