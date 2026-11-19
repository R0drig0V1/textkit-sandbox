import unicodedata
import unittest

from textkit.strings import slugify, squeeze


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


if __name__ == "__main__":
    unittest.main()
