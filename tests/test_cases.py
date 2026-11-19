"""Tests for textkit.cases, one TestCase class per public function."""

import unittest

from textkit.cases import to_snake_case

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


if __name__ == "__main__":
    unittest.main()
