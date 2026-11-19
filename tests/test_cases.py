"""Tests for textkit.cases. One TestCase class per public function.

ToSnakeCaseTest tests every row of the case table in ADR 0002
(docs/decisions/0002-splitting-runs-of-capitals.md) and checks that the table and CASES
below stay identical, so neither can change without the other.
"""

import ast
import pathlib
import re
import unittest

from textkit.cases import to_snake_case

ADR = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions" / (
    "0002-splitting-runs-of-capitals.md"
)

# (input, expected output), in the order of the ADR 0002 table.
CASES = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("IOError", "io_error"),
    ("ABC", "abc"),
    ("ABCd", "ab_cd"),
    ("URL2Path", "url2_path"),
    ("utf8Decode", "utf8_decode"),
    ("v2beta", "v2beta"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("mixed-kebab_snakeCase", "mixed_kebab_snake_case"),
    ("__init__", "init"),
    ("a--b__c", "a_b_c"),
    ("---", ""),
    ("aB", "a_b"),
    ("A", "a"),
    ("ÉtéCase", "été_case"),
]


def _adr_table() -> list[tuple[str, str]]:
    """Return the (input, output) rows of the case table in ADR 0002."""
    text = ADR.read_text(encoding="utf-8")
    rows = re.findall(r"^\| `(\".*?\")` \| `(\".*?\")` \|", text, re.M)
    return [(ast.literal_eval(a), ast.literal_eval(b)) for a, b in rows]


class ToSnakeCaseTest(unittest.TestCase):
    def test_every_case_of_adr_0002(self):
        for name, expected in CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_adr_table_matches_cases(self):
        self.assertEqual(_adr_table(), CASES)

    def test_table_has_the_cases_the_plan_requires(self):
        required = {"HTTPServer", "parseURL2", "camelCase", "PascalCase", "kebab-case",
                    "already_snake", ""}
        self.assertLessEqual(required, {name for name, _ in CASES})

    def test_other_characters_stay_in_their_word(self):
        self.assertEqual(to_snake_case("my var.Name"), "my var.name")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_snake_case(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
