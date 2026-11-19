"""Tests for textkit.cases, one TestCase class per public function."""

import unittest

from textkit.cases import to_camel_case, to_snake_case

# The case table of docs/decisions/0001-snake-case-word-boundaries.md, in the same order.
# Keep the two in sync: every row of the ADR is one entry here.
SNAKE_CASE_TABLE = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponse", "get_http_response"),
    ("HTTP2Server", "http2_server"),
    ("utf8Encode", "utf8_encode"),
    ("IOError", "io_error"),
    ("ABC", "abc"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("my-HTTPServer", "my_http_server"),
    ("_private", "_private"),
    ("parseURLs", "parse_ur_ls"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_case_table(self):
        for name, expected in SNAKE_CASE_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_non_ascii_letters_make_no_boundary(self):
        # Only ASCII capitals split words (ADR 0001); others are only lower-cased.
        self.assertEqual(to_snake_case("ÑandúÉclair"), "ñandúéclair")


class ToCamelCaseTest(unittest.TestCase):
    def test_snake_case(self):
        self.assertEqual(to_camel_case("user_id"), "userId")

    def test_kebab_case(self):
        self.assertEqual(to_camel_case("user-id"), "userId")

    def test_first_word_lower_cased_rest_capitalized(self):
        self.assertEqual(to_camel_case("HTTP_server"), "httpServer")
        self.assertEqual(to_camel_case("user_HTTP"), "userHttp")
        self.assertEqual(to_camel_case("SCREAMING_SNAKE_CASE"), "screamingSnakeCase")

    def test_mixed_separators(self):
        self.assertEqual(to_camel_case("my-user_id"), "myUserId")

    def test_run_of_separators_counts_as_one(self):
        self.assertEqual(to_camel_case("user__id"), "userId")
        self.assertEqual(to_camel_case("user-_-id"), "userId")

    def test_leading_and_trailing_separators_dropped(self):
        self.assertEqual(to_camel_case("_private"), "private")
        self.assertEqual(to_camel_case("__user_id__"), "userId")
        self.assertEqual(to_camel_case("-user-id-"), "userId")

    def test_no_separator_only_first_character_lower_cased(self):
        self.assertEqual(to_camel_case("userId"), "userId")
        self.assertEqual(to_camel_case("UserId"), "userId")
        self.assertEqual(to_camel_case("HTTPServer"), "hTTPServer")
        self.assertEqual(to_camel_case("x"), "x")
        self.assertEqual(to_camel_case("X"), "x")

    def test_empty_and_separators_only(self):
        self.assertEqual(to_camel_case(""), "")
        self.assertEqual(to_camel_case("_"), "")
        self.assertEqual(to_camel_case("-_-"), "")

    def test_digits(self):
        self.assertEqual(to_camel_case("utf8_encode"), "utf8Encode")
        self.assertEqual(to_camel_case("version_2"), "version2")


if __name__ == "__main__":
    unittest.main()
