import unittest

import unicodedata

from textkit.strings import slugify, squeeze


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_joins_words(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_removes_non_ascii_without_separator(self):
        self.assertEqual(slugify("na\u00efve"), "nave")

    def test_nfc_input_drops_precomposed_letters(self):
        text = unicodedata.normalize("NFC", "\u00d1and\u00fa")
        self.assertEqual(slugify(text), "and")

    def test_nfd_input_keeps_base_letters(self):
        text = unicodedata.normalize("NFD", "\u00d1and\u00fa")
        self.assertEqual(slugify(text), "nandu")

    def test_underscore_and_runs_become_one_hyphen(self):
        self.assertEqual(slugify("a__b --  c"), "a-b-c")

    def test_strips_hyphens_at_both_ends(self):
        self.assertEqual(slugify("--Hi--"), "hi")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Route 66"), "route-66")

    def test_non_ascii_that_lowercases_to_ascii_is_removed(self):
        # KELVIN SIGN lower-cases to "k"; it must be removed, not kept.
        self.assertEqual(slugify("\u212a9"), "9")

    def test_empty_and_punctuation_only_give_empty(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")


if __name__ == "__main__":
    unittest.main()
