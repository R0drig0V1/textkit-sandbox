"""Tests for textkit.strings."""

import unittest

from textkit.strings import slugify, squeeze


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_example_from_the_plan(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_punctuation_gives_empty_string(self):
        self.assertEqual(slugify("!?.,;:-_ \t\n"), "")

    def test_strips_leading_and_trailing_separators(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("  ...Hello World!!!  "), "hello-world")

    def test_collapses_every_separator_run_to_one_dash(self):
        self.assertEqual(slugify("a  -_- b"), "a-b")
        self.assertEqual(slugify("a\tb\nc"), "a-b-c")

    def test_keeps_digits(self):
        self.assertEqual(slugify("Top 10 Tips"), "top-10-tips")
        self.assertEqual(slugify("2024-01-02"), "2024-01-02")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_already_a_slug_is_unchanged(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_dropped_non_ascii_does_not_separate_words(self):
        self.assertEqual(slugify("aéb"), "ab")
        self.assertEqual(slugify("café au lait"), "caf-au-lait")
        self.assertEqual(slugify("a—b"), "ab")  # em dash is non-ASCII, so dropped

    def test_only_non_ascii_gives_empty_string(self):
        self.assertEqual(slugify("日本語"), "")

    def test_non_ascii_next_to_separators_leaves_no_stray_dash(self):
        self.assertEqual(slugify("é Hello é"), "hello")

    def test_non_ascii_with_ascii_lower_case_is_dropped(self):
        # The Kelvin sign lower-cases to ASCII "k"; it is dropped before lower-casing.
        self.assertEqual(slugify("K"), "")
        self.assertEqual(slugify("5K run"), "5-run")


if __name__ == "__main__":
    unittest.main()
