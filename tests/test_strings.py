import unittest

from textkit.strings import slugify, squeeze


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


if __name__ == "__main__":
    unittest.main()
