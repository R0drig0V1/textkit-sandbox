"""Tests for textkit.cases. One TestCase class per public function.

ToSnakeCaseTest tests every row of the case table in ADR 0002
(docs/decisions/0002-splitting-runs-of-capitals.md) and checks that the table and CASES
below stay identical, so neither can change without the other. ToCamelCaseTest tests every
example in the text of plan task T1.8 (docs/phases/phase-1-core-helpers.md).
"""

import ast
import pathlib
import re
import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case

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


class ToCamelCaseTest(unittest.TestCase):
    def test_examples_of_plan_task_t1_8(self):
        self.assertEqual(to_camel_case("user_id"), "userId")
        self.assertEqual(to_camel_case("HTTP_server"), "httpServer")

    def test_kebab_case(self):
        self.assertEqual(to_camel_case("kebab-case"), "kebabCase")
        self.assertEqual(to_camel_case("mixed-kebab_snake"), "mixedKebabSnake")

    def test_run_of_separators_counts_as_one(self):
        self.assertEqual(to_camel_case("a--b__c"), "aBC")
        self.assertEqual(to_camel_case("user_-_id"), "userId")

    def test_leading_and_trailing_separators_are_dropped(self):
        self.assertEqual(to_camel_case("__init__"), "init")
        self.assertEqual(to_camel_case("-user_id-"), "userId")

    def test_first_word_lower_cased_rest_capitalized(self):
        self.assertEqual(to_camel_case("SCREAMING_SNAKE"), "screamingSnake")
        self.assertEqual(to_camel_case("parse_URL2"), "parseUrl2")
        self.assertEqual(to_camel_case("v_2beta"), "v2beta")
        self.assertEqual(to_camel_case("été_case"), "étéCase")

    def test_no_separator_lower_cases_only_first_character(self):
        self.assertEqual(to_camel_case("userId"), "userId")
        self.assertEqual(to_camel_case("UserId"), "userId")
        self.assertEqual(to_camel_case("HTTPServer"), "hTTPServer")
        self.assertEqual(to_camel_case("A"), "a")
        self.assertEqual(to_camel_case("lower"), "lower")

    def test_leading_separator_counts_as_a_separator(self):
        self.assertEqual(to_camel_case("_userId"), "userid")

    def test_empty_and_separators_only(self):
        self.assertEqual(to_camel_case(""), "")
        self.assertEqual(to_camel_case("---"), "")
        self.assertEqual(to_camel_case("_-_"), "")

    def test_other_characters_stay_in_their_word(self):
        self.assertEqual(to_camel_case("my var_name.x"), "my varName.x")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_camel_case(None)  # type: ignore[arg-type]


class ToKebabCaseTest(unittest.TestCase):
    """to_kebab_case is to_snake_case with "_" replaced by "-" (plan task T2.3, ADR 0002)."""

    def test_every_case_of_adr_0002_converted(self):
        # CASES is kept equal to the ADR 0002 table by ToSnakeCaseTest.
        for name, snake in CASES:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), snake.replace("_", "-"))

    def test_examples_spelled_out(self):
        self.assertEqual(to_kebab_case("HTTPServer"), "http-server")
        self.assertEqual(to_kebab_case("parseURL2"), "parse-url2")
        self.assertEqual(to_kebab_case("camelCase"), "camel-case")
        self.assertEqual(to_kebab_case("already_snake"), "already-snake")
        self.assertEqual(to_kebab_case("kebab-case"), "kebab-case")
        self.assertEqual(to_kebab_case("mixed-kebab_snakeCase"), "mixed-kebab-snake-case")
        self.assertEqual(to_kebab_case("__init__"), "init")
        self.assertEqual(to_kebab_case(""), "")

    def test_other_characters_stay_in_their_word(self):
        self.assertEqual(to_kebab_case("my var.Name"), "my var.name")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_kebab_case(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
