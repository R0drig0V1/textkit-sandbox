"""Tests for textkit.plural: every row of the case table in
docs/decisions/0001-pluralize-rules.md, plus the failure mode."""

import unittest

from textkit.plural import pluralize

# The ADR's case table, row for row (input, expected output).
ADR_CASES = [
    ("cat", "cats"),
    ("bus", "buses"),
    ("box", "boxes"),
    ("buzz", "buzzes"),
    ("quiz", "quizzes"),
    ("church", "churches"),
    ("dish", "dishes"),
    ("city", "cities"),
    ("day", "days"),
    ("potato", "potatoes"),
    ("photo", "photos"),
    ("knife", "knives"),
    ("leaf", "leaves"),
    ("roof", "roofs"),
    ("child", "children"),
    ("Child", "Children"),
    ("CHILD", "CHILDREN"),
    ("person", "people"),
    ("sheep", "sheep"),
    ("SHEEP", "SHEEP"),
    ("Box", "Boxes"),
    ("CITY", "CITIES"),
    ("Knife", "Knives"),
    ("iPhone", "iPhones"),
    ("ñy", "ñys"),
    ("y", "ys"),
    ("a", "as"),
    ("", ""),
]


class PluralizeTest(unittest.TestCase):
    def test_adr_case_table(self):
        for word, expected in ADR_CASES:
            with self.subTest(word=word):
                self.assertEqual(pluralize(word), expected)

    def test_cli_argument_a(self):
        # Phase 3 rule: a one-parameter function is called with "a" in its own tests.
        self.assertEqual(pluralize("a"), "as")

    def test_mixed_case_irregular_follows_first_letter(self):
        self.assertEqual(pluralize("ChIlD"), "Children")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            pluralize(3)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
