"""Tests for textkit.cases. ToSnakeCaseTest asserts every row of ADR 0001's table of cases."""

import unittest

from textkit.cases import to_snake_case


class ToSnakeCaseTest(unittest.TestCase):
    # One row per line of the table at the end of
    # docs/decisions/0001-to-snake-case-word-boundaries.md; keep them in sync.
    ADR_TABLE = [
        ("HTTPServer", "http_server"),
        ("parseURL2", "parse_url2"),
        ("camelCase", "camel_case"),
        ("PascalCase", "pascal_case"),
        ("kebab-case", "kebab_case"),
        ("already_snake", "already_snake"),
        ("", ""),
        ("getHTTPResponseCode", "get_http_response_code"),
        ("XMLHttpRequest", "xml_http_request"),
        ("HTTP2Server", "http2_server"),
        ("base64Encode", "base64_encode"),
        ("IOError", "io_error"),
        ("getX", "get_x"),
        ("ABC", "abc"),
        ("ABCdef", "ab_cdef"),
        ("kebab--Case", "kebab_case"),
        ("snake_Case", "snake_case"),
        ("__init__", "init"),
        ("Ñandú", "ñandú"),
    ]

    def test_adr_table(self):
        for name, expected in self.ADR_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_snake_case_is_a_fixed_point(self):
        for name, _ in self.ADR_TABLE:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            to_snake_case(None)


if __name__ == "__main__":
    unittest.main()
