import random
import tracemalloc
import unittest

import unicodedata

from textkit.errors import InvalidValueError
from textkit.strings import center, dedent, is_palindrome, levenshtein, slug_title, slugify, squeeze, strip_accents, truncate, wrap


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
        with self.assertRaises(InvalidValueError):
            truncate("hello world", 2)

    def test_width_below_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(InvalidValueError):
            truncate("ab", 2)
        with self.assertRaises(InvalidValueError):
            truncate("", 0, suffix="...")

    def test_negative_width_raises(self):
        with self.assertRaises(InvalidValueError):
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
            with self.assertRaises(InvalidValueError):
                wrap("abc", width)
        with self.assertRaises(InvalidValueError):
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


class SlugTitleTest(unittest.TestCase):
    def test_character_cut_mid_word(self):
        self.assertEqual(slug_title("Hello, World!", 8), "hello-wo")

    def test_trailing_hyphen_stripped(self):
        self.assertEqual(slug_title("Hello, World!", 6), "hello")

    def test_whole_slug_fits(self):
        self.assertEqual(slug_title("Hello, World!", 11), "hello-world")
        self.assertEqual(slug_title("Hello, World!", 50), "hello-world")

    def test_zero_max_len_gives_empty(self):
        self.assertEqual(slug_title("x", 0), "")

    def test_punctuation_only_gives_empty(self):
        self.assertEqual(slug_title("!!!", 5), "")

    def test_never_longer_than_max_len(self):
        for n in range(0, 15):
            result = slug_title("Hello, World!", n)
            self.assertLessEqual(len(result), n)
            self.assertFalse(result.endswith("-"))

    def test_negative_max_len_raises(self):
        with self.assertRaises(InvalidValueError):
            slug_title("x", -1)
        with self.assertRaises(InvalidValueError):
            slug_title("", -1)


class IsPalindromeTest(unittest.TestCase):
    def test_classic_sentence(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama"))

    def test_accents_ignored(self):
        self.assertTrue(is_palindrome("Dábale arroz a la zorra el abad"))

    def test_nfd_input(self):
        text = unicodedata.normalize("NFD", "Dábale arroz a la zorra el abad")
        self.assertTrue(is_palindrome(text))

    def test_not_a_palindrome(self):
        self.assertFalse(is_palindrome("Hello, World!"))

    def test_digits_count(self):
        self.assertTrue(is_palindrome("12321"))
        self.assertFalse(is_palindrome("123"))
        self.assertFalse(is_palindrome("1a2"))

    def test_empty_is_palindrome(self):
        self.assertTrue(is_palindrome(""))

    def test_no_alphanumerics_is_palindrome(self):
        self.assertTrue(is_palindrome("!!! ,, ?"))
        self.assertTrue(is_palindrome("   "))

    def test_underscore_ignored(self):
        self.assertTrue(is_palindrome("a_b_a_"))

    def test_single_character(self):
        self.assertTrue(is_palindrome("x"))

    def test_casefold_not_lower(self):
        # casefold turns "ß" into "ss", so "ßs" becomes "sss"; lower() would keep "ßs".
        self.assertTrue(is_palindrome("ßs"))

    def test_non_ascii_letters_count(self):
        self.assertTrue(is_palindrome("øxø"))
        self.assertFalse(is_palindrome("øx"))


class DedentTest(unittest.TestCase):
    def test_removes_common_prefix(self):
        self.assertEqual(dedent("    a\n      b\n"), "a\n  b\n")

    def test_empty_text(self):
        self.assertEqual(dedent(""), "")

    def test_no_common_prefix_unchanged(self):
        self.assertEqual(dedent("a\n  b\n"), "a\n  b\n")

    def test_tab_and_space_are_different(self):
        self.assertEqual(dedent("\ta\n    b\n"), "\ta\n    b\n")
        self.assertEqual(dedent(" \ta\n  b\n"), "\ta\n b\n")

    def test_common_tab_prefix(self):
        self.assertEqual(dedent("\t\ta\n\tb\n"), "\ta\nb\n")

    def test_no_final_newline(self):
        self.assertEqual(dedent("  a\n    b"), "a\n  b")

    def test_crlf_endings_kept(self):
        self.assertEqual(dedent("  a\r\n    b\r\n"), "a\r\n  b\r\n")

    def test_form_feed_ends_a_line(self):
        # splitlines treats "\x0c" as a line ending: "  b" is a line of its own.
        self.assertEqual(dedent("  a\x0c  b\n"), "a\x0cb\n")

    def test_next_line_ends_a_line(self):
        self.assertEqual(dedent("  a\x85  b"), "a\x85b")

    def test_blank_lines_ignored_and_emptied(self):
        self.assertEqual(dedent("    a\n \t \n\n    b\n"), "a\n\n\nb\n")

    def test_blank_last_line(self):
        self.assertEqual(dedent("  a\n  b\n  "), "a\nb\n")
        self.assertEqual(dedent("  a\n  b\n  \n"), "a\nb\n\n")

    def test_blank_line_ending_kept(self):
        self.assertEqual(dedent("  a\r\n  \r\n  b"), "a\r\n\r\nb")

    def test_only_blank_lines(self):
        self.assertEqual(dedent("  \n\t\r\n"), "\n\r\n")

    def test_other_whitespace_not_part_of_prefix(self):
        self.assertEqual(dedent("  \u3000a\n  b\n"), "\u3000a\nb\n")

    def test_trailing_spaces_kept(self):
        self.assertEqual(dedent("  a  \n  b\t\n"), "a  \nb\t\n")


class CenterTest(unittest.TestCase):
    def test_odd_padding_extra_on_right(self):
        # str.center gives "  ab " here: the extra space on the left.
        self.assertEqual(center("ab", 5), " ab  ")
        self.assertNotEqual(center("ab", 5), "ab".center(5))

    def test_odd_padding_odd_text(self):
        self.assertEqual(center("abc", 6), " abc  ")

    def test_extra_always_on_right(self):
        # Non-empty texts only: "" has no left/right split (test_empty_text covers it).
        for text in ("a", "ab", "abc", "abcd"):
            for width in range(len(text), len(text) + 8):
                with self.subTest(text=text, width=width):
                    # A fill that no text contains, so the left padding is countable.
                    result = center(text, width, "*")
                    self.assertEqual(len(result), width)
                    left = len(result) - len(result.lstrip("*"))
                    right = width - len(text) - left
                    self.assertIn(right - left, (0, 1))
                    self.assertEqual(result[left : left + len(text)], text)

    def test_even_padding_is_symmetric(self):
        self.assertEqual(center("ab", 6), "  ab  ")

    def test_custom_fill(self):
        self.assertEqual(center("ab", 5, "*"), "*ab**")
        self.assertEqual(center("x", 4, "-"), "-x--")

    def test_non_ascii_fill_and_text(self):
        self.assertEqual(center("ñ", 4, "·"), "·ñ··")

    def test_empty_text(self):
        self.assertEqual(center("", 3, "*"), "***")
        self.assertEqual(center("", 0), "")

    def test_text_of_width_unchanged(self):
        self.assertEqual(center("abc", 3), "abc")

    def test_longer_text_unchanged(self):
        self.assertEqual(center("abcdef", 3), "abcdef")
        self.assertEqual(center("abc", 0), "abc")

    def test_fill_not_one_character_raises(self):
        for fill in ("", "ab", "**"):
            with self.subTest(fill=fill):
                with self.assertRaises(InvalidValueError):
                    center("ab", 5, fill)

    def test_negative_width_raises(self):
        with self.assertRaises(InvalidValueError):
            center("ab", -1)

    def test_checks_come_first_even_for_long_text(self):
        with self.assertRaises(InvalidValueError):
            center("abcdef", 3, "")
        with self.assertRaises(InvalidValueError):
            center("abcdef", -1)
        with self.assertRaises(InvalidValueError):
            center("", -1)


def _full_table_levenshtein(a, b):
    """Reference edit distance with the whole (len(a) + 1) x (len(b) + 1) table."""
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        table[i][0] = i
    for j in range(len(b) + 1):
        table[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            table[i][j] = min(
                table[i - 1][j] + 1,
                table[i][j - 1] + 1,
                table[i - 1][j - 1] + (a[i - 1] != b[j - 1]),
            )
    return table[len(a)][len(b)]


class LevenshteinTest(unittest.TestCase):
    def test_kitten_sitting(self):
        self.assertEqual(levenshtein("kitten", "sitting"), 3)

    def test_symmetric(self):
        pairs = [("kitten", "sitting"), ("flaw", "lawn"), ("", "abc"), ("abc", "abd"),
                 ("intention", "execution")]
        for a, b in pairs:
            with self.subTest(a=a, b=b):
                self.assertEqual(levenshtein(a, b), levenshtein(b, a))

    def test_empty_gives_length(self):
        for s in ["", "a", "abc", "Ñandú", "\U0001F600x"]:
            with self.subTest(s=s):
                self.assertEqual(levenshtein("", s), len(s))
                self.assertEqual(levenshtein(s, ""), len(s))

    def test_equal_texts_are_zero(self):
        self.assertEqual(levenshtein("textkit", "textkit"), 0)

    def test_each_operation_costs_one(self):
        self.assertEqual(levenshtein("abc", "abxc"), 1)  # insert
        self.assertEqual(levenshtein("abc", "ac"), 1)  # delete
        self.assertEqual(levenshtein("abc", "abd"), 1)  # substitute

    def test_case_sensitive(self):
        self.assertEqual(levenshtein("Abc", "abc"), 1)

    def test_code_points_not_bytes(self):
        # One astral character is one code point (four UTF-8 bytes, two UTF-16 units).
        self.assertEqual(levenshtein("a\U0001F600b", "ab"), 1)
        self.assertEqual(levenshtein("\u00f1", "n"), 1)

    def test_no_normalization(self):
        # NFC "\u00e9" against NFD "e\u0301": substitute one, insert the other.
        self.assertEqual(levenshtein("\u00e9", "e\u0301"), 2)

    def test_matches_full_table_on_random_pairs(self):
        rng = random.Random(310)
        for _ in range(200):
            a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 12)))
            b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 12)))
            with self.subTest(a=a, b=b):
                self.assertEqual(levenshtein(a, b), _full_table_levenshtein(a, b))

    def test_two_rows_of_memory(self):
        # A full table for two 1000-character texts holds a million entries (several MB);
        # two rows hold about 2000, far under the 1 MB bound.
        rng = random.Random(1000)
        a = "".join(rng.choice("abcdefghij") for _ in range(1000))
        b = "".join(rng.choice("abcdefghij") for _ in range(1000))
        tracemalloc.start()
        try:
            baseline, _ = tracemalloc.get_traced_memory()
            distance = levenshtein(a, b)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(peak - baseline, 1_000_000)
        self.assertGreater(distance, 0)
        self.assertLessEqual(distance, 1000)


if __name__ == "__main__":
    unittest.main()
