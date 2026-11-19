"""Tests for textkit.plural, one TestCase class per public function.

PluralizeTest tests every row of the case table that ends the plural ADR
(docs/decisions/*-pluralize-rules.md) and checks that the table and CASES stay identical, so
neither can drift from the other. It also checks that the minimum rows of plan task T3.6 are
in the table, that every irregular entry keeps the case rule in its three casings, and the
phase-3 rule that a call with "a" never raises.
"""

import ast
import pathlib
import re
import unittest

from textkit.plural import _IRREGULAR, pluralize

# Mirror of the case table in docs/decisions/*-pluralize-rules.md: (input, plural).
CASES = [
    ("", ""),
    ("cat", "cats"),
    ("bus", "buses"),
    ("box", "boxes"),
    ("buzz", "buzzes"),
    ("waltz", "waltzes"),
    ("quiz", "quizzes"),
    ("church", "churches"),
    ("dish", "dishes"),
    ("city", "cities"),
    ("day", "days"),
    ("toy", "toys"),
    ("y", "ys"),
    ("potato", "potatoes"),
    ("photo", "photos"),
    ("knife", "knives"),
    ("roof", "roofs"),
    ("child", "children"),
    ("Child", "Children"),
    ("CHILD", "CHILDREN"),
    ("Man", "Men"),
    ("person", "people"),
    ("mouse", "mice"),
    ("sheep", "sheep"),
    ("SHEEP", "SHEEP"),
    ("CITY", "CITIES"),
    ("City", "Cities"),
    ("BOX", "BOXES"),
    ("iPhone", "iPhones"),
    ("a", "as"),
    ("café", "cafés"),
    ("stomach", "stomaches"),
    ("cats", "catses"),
    ("my child", "my childs"),
    ("123", "123s"),
]

# Rows plan task T3.6 (docs/phases/phase-3-converters.md) requires in the ADR table.
PLAN_MINIMUM_ROWS = [
    "cat", "bus", "box", "buzz", "quiz", "church", "dish", "city", "day", "potato",
    "photo", "knife", "child", "Child", "CHILD", "sheep", "",
]

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _adr_cases() -> list:
    """Parse the case table of the plural ADR. Glob on the slug: the number may change at merge."""
    (adr,) = sorted((_ROOT / "docs" / "decisions").glob("*-pluralize-rules.md"))
    rows = re.findall(r"^\| `(.*?)` \| `(.*?)` \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(word), ast.literal_eval(plural)) for word, plural in rows]


class PluralizeTest(unittest.TestCase):
    def test_adr_table(self):
        for word, expected in CASES:
            with self.subTest(word=word):
                self.assertEqual(pluralize(word), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), CASES)

    def test_plan_minimum_rows_in_table(self):
        words = [word for word, _ in CASES]
        self.assertEqual([w for w in PLAN_MINIMUM_ROWS if w not in words], [])

    def test_irregular_table_in_three_casings(self):
        for singular, plural in sorted(_IRREGULAR.items()):
            with self.subTest(word=singular):
                self.assertEqual(pluralize(singular), plural)
                self.assertEqual(pluralize(singular.upper()), plural.upper())
                self.assertEqual(
                    pluralize(singular.capitalize()), plural[:1].upper() + plural[1:]
                )

    def test_cli_argument_does_not_raise(self):
        # Phase-3 rule: T2.6's CLI calls every one-parameter function with "a".
        self.assertEqual(pluralize("a"), "as")

    def test_rejects_non_str(self):
        for value in (None, 1, b"cat", ["cat"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    pluralize(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
