import unittest

import unicodedata

from textkit.strings import slugify, squeeze


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


if __name__ == "__main__":
    unittest.main()
