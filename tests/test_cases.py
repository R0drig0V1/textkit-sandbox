"""Tests for textkit.cases. The table cases mirror docs/decisions/0001-snake-case-capital-runs.md."""

import unittest

from textkit.cases import to_kebab_case, to_snake_case


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


if __name__ == "__main__":
    unittest.main()
