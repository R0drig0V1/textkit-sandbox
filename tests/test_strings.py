"""Tests for textkit.strings: one TestCase class per public function."""

import unittest

import unicodedata

from textkit.strings import slugify, squeeze, strip_accents


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_joins_words(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input_drops_precomposed_letters(self):
        self.assertEqual(slugify("Ñandú"), "and")  # "Ñandú", NFC as typed

    def test_nfd_input_keeps_base_letters(self):
        self.assertEqual(slugify("Ñandú"), "nandu")  # "Ñandú", NFD

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_separators(self):
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_run_of_mixed_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  _-!? b"), "a-b")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--Hello--"), "hello")

    def test_digits_kept(self):
        self.assertEqual(slugify("Python 3.9"), "python-3-9")

    def test_non_ascii_removed_before_lowercasing(self):
        # U+212A KELVIN SIGN lower-cases to ASCII "k"; it must be removed, not kept.
        self.assertEqual(slugify("5K run"), "5-run")


class StripAccentsTest(unittest.TestCase):
    def test_plan_example(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_nfd_input_gives_same_result(self):
        self.assertEqual(strip_accents(unicodedata.normalize("NFD", "Ñandú")), "Nandu")

    def test_several_marks(self):
        self.assertEqual(strip_accents("crème brûlée, naïve, Ångström"),
                         "creme brulee, naive, Angstrom")

    def test_stacked_marks_on_one_letter(self):
        # "ệ" carries two marks (circumflex and dot below).
        self.assertEqual(strip_accents("Việt"), "Viet")

    def test_letters_without_combining_marks_are_kept(self):
        self.assertEqual(strip_accents("ø ł ß"), "ø ł ß")

    def test_plain_and_empty_text_unchanged(self):
        self.assertEqual(strip_accents("plain ASCII 123"), "plain ASCII 123")
        self.assertEqual(strip_accents(""), "")

    def test_lone_combining_mark_removed(self):
        self.assertEqual(strip_accents("a\u0301\u0301"), "a")

    def test_non_mark_decompositions_are_recomposed(self):
        self.assertEqual(strip_accents("한국어"), "한국어")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            strip_accents(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
