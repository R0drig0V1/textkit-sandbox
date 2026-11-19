"""Tests for textkit.cases, one TestCase class per public function."""

import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case

# Every row of the case table in docs/decisions/0002-snake-case-word-splitting.md, in order.
# Keep the two in sync: a row added to the ADR is added here, and the reverse.
ADR_0002_TABLE = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("HTTP2Server", "http2_server"),
    ("Version2Beta", "version2_beta"),
    ("userID", "user_id"),
    ("ABC", "abc"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("kebab-Case", "kebab_case"),
    ("a--b", "a_b"),
    ("_private", "private"),
    ("-", ""),
    ("iOS", "i_os"),
    ("hello world", "hello world"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_table(self):
        for name, expected in ADR_0002_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_snake_case_output_is_a_fixed_point(self):
        # Converting the output again changes nothing: snake_case input comes back unchanged.
        for name, _ in ADR_0002_TABLE:
            once = to_snake_case(name)
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(once), once)

    def test_trailing_and_mixed_separators_are_dropped_or_merged(self):
        self.assertEqual(to_snake_case("__dunder__"), "dunder")
        self.assertEqual(to_snake_case("mixed-_-separators"), "mixed_separators")

    def test_non_ascii_letters_are_lower_cased_but_never_split(self):
        self.assertEqual(to_snake_case("ÉcoleNormale"), "école_normale")
        self.assertEqual(to_snake_case("naïveÉcole"), "naïveécole")


class ToCamelCaseTest(unittest.TestCase):
    def test_plan_examples(self):
        self.assertEqual(to_camel_case("user_id"), "userId")
        self.assertEqual(to_camel_case("HTTP_server"), "httpServer")

    def test_snake_and_kebab_case(self):
        self.assertEqual(to_camel_case("kebab-case"), "kebabCase")
        self.assertEqual(to_camel_case("get_http_response_code"), "getHttpResponseCode")
        self.assertEqual(to_camel_case("mixed-_separators"), "mixedSeparators")

    def test_first_word_lower_cased_and_the_rest_capitalized(self):
        self.assertEqual(to_camel_case("SCREAMING_SNAKE"), "screamingSnake")
        self.assertEqual(to_camel_case("user_ID"), "userId")
        # Inner capitals of a word after a separator are lower-cased too.
        self.assertEqual(to_camel_case("my_camelCase"), "myCamelcase")

    def test_runs_of_separators_count_as_one(self):
        self.assertEqual(to_camel_case("a--b"), "aB")
        self.assertEqual(to_camel_case("a__b-_-c"), "aBC")

    def test_leading_and_trailing_separators_are_dropped(self):
        self.assertEqual(to_camel_case("_private"), "private")
        self.assertEqual(to_camel_case("__dunder__"), "dunder")
        self.assertEqual(to_camel_case("-kebab-case-"), "kebabCase")

    def test_no_separator_only_lower_cases_the_first_character(self):
        self.assertEqual(to_camel_case("camelCase"), "camelCase")
        self.assertEqual(to_camel_case("PascalCase"), "pascalCase")
        self.assertEqual(to_camel_case("HTTPServer"), "hTTPServer")
        self.assertEqual(to_camel_case("x"), "x")
        self.assertEqual(to_camel_case("X"), "x")

    def test_empty_and_separators_only(self):
        self.assertEqual(to_camel_case(""), "")
        self.assertEqual(to_camel_case("-"), "")
        self.assertEqual(to_camel_case("_-_"), "")

    def test_digits_and_non_separators(self):
        self.assertEqual(to_camel_case("version_2"), "version2")
        self.assertEqual(to_camel_case("base64_encode"), "base64Encode")
        # Spaces are not separators (as in ADR 0002).
        self.assertEqual(to_camel_case("hello world"), "hello world")
        self.assertEqual(to_camel_case("ÉCOLE_normale"), "écoleNormale")


class ToKebabCaseTest(unittest.TestCase):
    def test_adr_table_in_kebab_case(self):
        # Every row of ADR 0002, with the expected snake_case output written in kebab-case.
        for name, expected in ADR_0002_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), expected.replace("_", "-"))

    def test_adr_table_explicit_rows(self):
        # A few rows spelled out, so a bug in the conversion of the table cannot hide one.
        self.assertEqual(to_kebab_case("HTTPServer"), "http-server")
        self.assertEqual(to_kebab_case("getHTTPResponseCode"), "get-http-response-code")
        self.assertEqual(to_kebab_case("parseURL2"), "parse-url2")
        self.assertEqual(to_kebab_case("already_snake"), "already-snake")
        self.assertEqual(to_kebab_case("SCREAMING_SNAKE"), "screaming-snake")

    def test_kebab_case_output_is_a_fixed_point(self):
        for name, _ in ADR_0002_TABLE:
            once = to_kebab_case(name)
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(once), once)

    def test_separators_are_merged_or_dropped(self):
        self.assertEqual(to_kebab_case("__dunder__"), "dunder")
        self.assertEqual(to_kebab_case("-kebab-case-"), "kebab-case")
        self.assertEqual(to_kebab_case("mixed-_-separators"), "mixed-separators")
        self.assertEqual(to_kebab_case("_-_"), "")

    def test_non_ascii_letters_are_lower_cased_but_never_split(self):
        self.assertEqual(to_kebab_case("ÉcoleNormale"), "école-normale")
        self.assertEqual(to_kebab_case("naïveÉcole"), "naïveécole")


if __name__ == "__main__":
    unittest.main()
