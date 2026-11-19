"""Tests for textkit.cases. ToSnakeCaseTest and ToKebabCaseTest cover every row of the case
table in docs/decisions/0003-snake-case-capital-runs.md, in the same order; ToCamelCaseTest
covers the rules of plan task T1.8 (docs/phases/phase-1-core-helpers.md)."""

import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case

# The ADR's case table (input -> output). Keep the two in sync.
ADR_CASES = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("HTTP2Server", "http2_server"),
    ("version2Beta", "version2_beta"),
    ("ABC", "abc"),
    ("iPhone", "i_phone"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("HTTP_server", "http_server"),
    ("kebab--snake__mixed-_case", "kebab_snake_mixed_case"),
    ("-leading_and_trailing-", "leading_and_trailing"),
    ("utf8string", "utf8string"),
    ("ÉtéCase", "étécase"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_case_table(self):
        for name, expected in ADR_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_is_idempotent(self):
        for name, _ in ADR_CASES:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)


class ToCamelCaseTest(unittest.TestCase):
    def test_snake_case(self):
        self.assertEqual(to_camel_case("user_id"), "userId")
        self.assertEqual(to_camel_case("parse_http_response"), "parseHttpResponse")

    def test_kebab_case(self):
        self.assertEqual(to_camel_case("user-id"), "userId")

    def test_first_word_lower_rest_capitalized(self):
        self.assertEqual(to_camel_case("HTTP_server"), "httpServer")
        self.assertEqual(to_camel_case("SCREAMING_SNAKE_CASE"), "screamingSnakeCase")
        self.assertEqual(to_camel_case("user_ID"), "userId")

    def test_separator_run_counts_as_one(self):
        self.assertEqual(to_camel_case("user__id"), "userId")
        self.assertEqual(to_camel_case("kebab--snake__mixed-_case"), "kebabSnakeMixedCase")

    def test_leading_and_trailing_separators_dropped(self):
        self.assertEqual(to_camel_case("_user_id_"), "userId")
        self.assertEqual(to_camel_case("--user-id--"), "userId")
        self.assertEqual(to_camel_case("__init__"), "init")

    def test_no_separator_lowers_only_first_character(self):
        self.assertEqual(to_camel_case("user"), "user")
        self.assertEqual(to_camel_case("PascalCase"), "pascalCase")
        self.assertEqual(to_camel_case("camelCase"), "camelCase")
        self.assertEqual(to_camel_case("HTTPServer"), "hTTPServer")
        self.assertEqual(to_camel_case("X"), "x")

    def test_digits(self):
        self.assertEqual(to_camel_case("version_2_beta"), "version2Beta")
        self.assertEqual(to_camel_case("utf8_string"), "utf8String")

    def test_empty_and_separators_only(self):
        self.assertEqual(to_camel_case(""), "")
        self.assertEqual(to_camel_case("_"), "")
        self.assertEqual(to_camel_case("-_-"), "")

    def test_non_ascii_words(self):
        self.assertEqual(to_camel_case("été_case"), "étéCase")


class ToKebabCaseTest(unittest.TestCase):
    def test_adr_case_table(self):
        # Same word boundaries as to_snake_case, joined with "-": the expected output is the
        # ADR's snake_case output with "_" swapped for "-".
        for name, snake in ADR_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), snake.replace("_", "-"))

    def test_examples(self):
        self.assertEqual(to_kebab_case("HTTPServer"), "http-server")
        self.assertEqual(to_kebab_case("getHTTPResponseCode"), "get-http-response-code")
        self.assertEqual(to_kebab_case("kebab--snake__mixed-_case"), "kebab-snake-mixed-case")
        self.assertEqual(to_kebab_case("-leading_and_trailing-"), "leading-and-trailing")

    def test_is_idempotent(self):
        for name, _ in ADR_CASES:
            with self.subTest(name=name):
                once = to_kebab_case(name)
                self.assertEqual(to_kebab_case(once), once)


if __name__ == "__main__":
    unittest.main()
