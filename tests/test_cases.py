"""Tests for textkit.cases, one TestCase class per public function."""

import unittest

from textkit.cases import to_snake_case

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


if __name__ == "__main__":
    unittest.main()
