"""Tests for textkit.cases: one TestCase class per public function."""

import unittest

from textkit.cases import to_camel_case, to_snake_case

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


class ToCamelCaseTest(unittest.TestCase):
    def test_snake_and_kebab_case(self):
        cases = [
            ("user_id", "userId"),
            ("user-id", "userId"),
            ("first_name_last", "firstNameLast"),
            ("mixed-styles_here", "mixedStylesHere"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_first_word_lowered_rest_capitalized(self):
        cases = [
            ("HTTP_server", "httpServer"),
            ("user_ID", "userId"),
            ("Kebab-Case-Name", "kebabCaseName"),
            ("SCREAMING_SNAKE", "screamingSnake"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_runs_of_separators_count_as_one(self):
        cases = [("a--b__c", "aBC"), ("user_-_id", "userId"), ("a_-b", "aB")]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_leading_and_trailing_separators_dropped(self):
        cases = [("_private", "private"), ("__init__", "init"), ("-user-id-", "userId"),
                 ("_Private_Name", "privateName")]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_no_separator_lowers_only_first_character(self):
        cases = [
            ("PascalCase", "pascalCase"),
            ("camelCase", "camelCase"),
            ("HTTPServer", "hTTPServer"),
            ("HTTP", "hTTP"),
            ("user", "user"),
            ("X", "x"),
            ("Été", "été"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_empty_and_separators_only(self):
        for name in ("", "_", "-", "__", "-_-"):
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), "")

    def test_digits_and_other_characters_are_kept(self):
        cases = [("user_2fa", "user2fa"), ("vector_3d", "vector3d"), ("a b_c", "a bC")]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_rejects_non_str(self):
        for value in (None, 42, b"user_id"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_camel_case(value)


if __name__ == "__main__":
    unittest.main()
