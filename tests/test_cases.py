"""Tests for textkit.cases. CASES mirrors the table at the end of ADR 0001, row by row."""

import unittest

from textkit.cases import to_snake_case

# (input, expected) in the order of the table in
# docs/decisions/0001-to-snake-case-word-boundaries.md; keep both in sync.
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
    ("HTTP2Server", "http2_server"),
    ("utf8Decoder", "utf8_decoder"),
    ("ABC", "abc"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("mixed-Kebab_snakeCase", "mixed_kebab_snake_case"),
    ("__private--name__", "private_name"),
    ("--", ""),
    ("ÉcoleNormale", "école_normale"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_table(self):
        for name, expected in CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_idempotent(self):
        for name, _ in CASES:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)


if __name__ == "__main__":
    unittest.main()
