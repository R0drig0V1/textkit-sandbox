"""Tests for textkit.cases, one TestCase per function.

ToSnakeCaseTest asserts every row of ADR 0001's table of cases; ToCamelCaseTest covers the
T1.8 rules for to_camel_case; ToKebabCaseTest asserts the same ADR 0001 rows with ``_``
replaced by ``-`` (T2.3).
"""

import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case


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



class ToCamelCaseTest(unittest.TestCase):
    def assertCases(self, cases):
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_snake_and_kebab_case(self):
        self.assertCases([
            ("user_id", "userId"),
            ("kebab-case", "kebabCase"),
            ("user_account_id", "userAccountId"),
            ("mixed_-sep", "mixedSep"),
        ])

    def test_first_word_lower_cased_rest_capitalized(self):
        self.assertCases([
            ("HTTP_server", "httpServer"),
            ("user_ID", "userId"),
            ("Parse-URL", "parseUrl"),
        ])

    def test_run_of_separators_counts_as_one(self):
        self.assertCases([
            ("user__id", "userId"),
            ("a__b--c", "aBC"),
            ("kebab--Case", "kebabCase"),
        ])

    def test_leading_and_trailing_separators_dropped(self):
        self.assertCases([
            ("__init__", "init"),
            ("_private_name", "privateName"),
            ("-user-id-", "userId"),
        ])

    def test_no_separator_only_first_character_lower_cased(self):
        self.assertCases([
            ("camelCase", "camelCase"),
            ("PascalCase", "pascalCase"),
            ("HTTP", "hTTP"),
            ("X", "x"),
            ("word", "word"),
        ])

    def test_empty_and_separators_only(self):
        self.assertCases([("", ""), ("_", ""), ("--", ""), ("_-_", "")])

    def test_digits_kept(self):
        self.assertCases([("utf_8", "utf8"), ("base64_encode", "base64Encode"), ("v2_api", "v2Api")])

    def test_round_trips_simple_snake_case(self):
        for name in ["user_id", "parse_url2", "base64_encode"]:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(to_camel_case(name)), name)

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            to_camel_case(None)



class ToKebabCaseTest(unittest.TestCase):
    def test_adr_table(self):
        # ADR 0001, Consequences: to_kebab_case inherits every row with "_" replaced by "-".
        for name, snake in ToSnakeCaseTest.ADR_TABLE:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), snake.replace("_", "-"))

    def test_kebab_case_is_a_fixed_point(self):
        for name, _ in ToSnakeCaseTest.ADR_TABLE:
            with self.subTest(name=name):
                once = to_kebab_case(name)
                self.assertEqual(to_kebab_case(once), once)

    def test_snake_and_kebab_input(self):
        for name, expected in [
            ("already_snake", "already-snake"),
            ("already-kebab", "already-kebab"),
            ("mixed_-sep", "mixed-sep"),
            ("-user-id-", "user-id"),
        ]:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), expected)

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            to_kebab_case(None)


if __name__ == "__main__":
    unittest.main()
