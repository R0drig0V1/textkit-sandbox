"""Tests for textkit.cases."""
import unittest

from textkit.cases import to_snake_case

# The table of cases at the end of docs/decisions/0001-to-snake-case-word-boundaries.md,
# row by row and in the same order. Keep both in sync.
ADR_CASES = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("URL2Path", "url2_path"),
    ("utf8Encode", "utf8_encode"),
    ("IOError", "io_error"),
    ("ABC", "abc"),
    ("A", "a"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("mixed-kebab_snake", "mixed_kebab_snake"),
    ("--leading--trailing--", "leading_trailing"),
    ("hello world", "hello_world"),
    ("PDFs", "pd_fs"),
    ("ÉtéChaud", "été_chaud"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_table(self):
        for name, expected in ADR_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_separators_only_give_empty_string(self):
        self.assertEqual(to_snake_case("-_-"), "")

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            to_snake_case(None)


if __name__ == "__main__":
    unittest.main()
