"""Tests for textkit.cases: one TestCase class per public function."""

import unittest

from textkit.cases import to_snake_case

# The table of cases of ADR 0001 (docs/decisions/0001-to-snake-case-capital-runs.md), row by
# row and in the same order: keep both in sync.
ADR_0001_CASES = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("parseURL", "parse_url"),
    ("utf8Encode", "utf8_encode"),
    ("Vector3D", "vector3_d"),
    ("IOError", "io_error"),
    ("ABCdef", "ab_cdef"),
    ("HTTP", "http"),
    ("Kebab-Case-Name", "kebab_case_name"),
    ("mixed-styles_andCase", "mixed_styles_and_case"),
    ("__init__", "init"),
    ("a--b__c", "a_b_c"),
    ("-", ""),
    ("ÉtéÀ", "été_à"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_0001_table(self):
        for name, expected in ADR_0001_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_snake_case_is_a_fixed_point(self):
        for name, _ in ADR_0001_CASES:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)

    def test_rejects_non_str(self):
        for value in (None, 42, b"camelCase"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_snake_case(value)


if __name__ == "__main__":
    unittest.main()
