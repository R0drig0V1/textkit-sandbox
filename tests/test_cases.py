"""Tests for textkit.cases. The table cases mirror docs/decisions/0001-snake-case-capital-runs.md."""

import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case


class ToSnakeCaseTest(unittest.TestCase):
    # One entry per row of the case table in ADR 0001, in the same order.
    ADR_TABLE = [
        ("HTTPServer", "http_server"),
        ("parseURL2", "parse_url2"),
        ("camelCase", "camel_case"),
        ("PascalCase", "pascal_case"),
        ("kebab-case", "kebab_case"),
        ("already_snake", "already_snake"),
        ("", ""),
        ("getHTTPResponseCode", "get_http_response_code"),
        ("URL2Parser", "url2_parser"),
        ("version2Beta", "version2_beta"),
        ("HTTP", "http"),
        ("A", "a"),
        ("Already_Snake", "already_snake"),
        ("kebab--case", "kebab_case"),
        ("-leading-and-trailing-", "leading_and_trailing"),
        ("mixed-kebab_snakeCase", "mixed_kebab_snake_case"),
    ]

    def test_adr_table(self):
        for name, expected in self.ADR_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_idempotent(self):
        for name, _ in self.ADR_TABLE:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)

    def test_other_characters_are_kept(self):
        self.assertEqual(to_snake_case("Foo Bar"), "foo bar")


class ToKebabCaseTest(unittest.TestCase):
    # Every ADR 0001 row, through to_kebab_case: the same words joined by "-".
    def test_adr_table(self):
        for name, snake in ToSnakeCaseTest.ADR_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), snake.replace("_", "-"))

    def test_examples(self):
        cases = [
            ("HTTPServer", "http-server"),
            ("parseURL2", "parse-url2"),
            ("snake_case_name", "snake-case-name"),
            ("already-kebab", "already-kebab"),
            ("__dunder__", "dunder"),
            ("mixed-kebab_snakeCase", "mixed-kebab-snake-case"),
            ("", ""),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), expected)

    def test_idempotent(self):
        for name, _ in ToSnakeCaseTest.ADR_TABLE:
            with self.subTest(name=name):
                once = to_kebab_case(name)
                self.assertEqual(to_kebab_case(once), once)

    def test_other_characters_are_kept(self):
        self.assertEqual(to_kebab_case("Foo Bar"), "foo bar")


class ToCamelCaseTest(unittest.TestCase):
    def test_snake_case(self):
        self.assertEqual(to_camel_case("user_id"), "userId")
        self.assertEqual(to_camel_case("get_http_response_code"), "getHttpResponseCode")

    def test_kebab_case(self):
        self.assertEqual(to_camel_case("kebab-case"), "kebabCase")
        self.assertEqual(to_camel_case("mixed-kebab_snake"), "mixedKebabSnake")

    def test_first_word_lowered_rest_capitalized(self):
        self.assertEqual(to_camel_case("HTTP_server"), "httpServer")
        self.assertEqual(to_camel_case("User_ID"), "userId")
        self.assertEqual(to_camel_case("parse_URL2"), "parseUrl2")

    def test_run_of_separators_counts_as_one(self):
        self.assertEqual(to_camel_case("user__id"), "userId")
        self.assertEqual(to_camel_case("user-_-id"), "userId")

    def test_leading_and_trailing_separators_dropped(self):
        self.assertEqual(to_camel_case("_private"), "private")
        self.assertEqual(to_camel_case("-leading-and-trailing-"), "leadingAndTrailing")
        self.assertEqual(to_camel_case("__User_id__"), "userId")

    def test_no_separator_lowers_first_character_only(self):
        self.assertEqual(to_camel_case("userId"), "userId")
        self.assertEqual(to_camel_case("UserId"), "userId")
        self.assertEqual(to_camel_case("HTTP"), "hTTP")
        self.assertEqual(to_camel_case("A"), "a")
        self.assertEqual(to_camel_case("word"), "word")

    def test_empty_and_separators_only(self):
        self.assertEqual(to_camel_case(""), "")
        self.assertEqual(to_camel_case("_"), "")
        self.assertEqual(to_camel_case("-_-"), "")

    def test_digits_and_other_characters_kept_in_word(self):
        self.assertEqual(to_camel_case("version_2_beta"), "version2Beta")
        self.assertEqual(to_camel_case("foo bar_baz"), "foo barBaz")


if __name__ == "__main__":
    unittest.main()
