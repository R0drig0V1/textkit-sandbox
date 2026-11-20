"""Tests for textkit.cases."""
import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case

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


class ToCamelCaseTest(unittest.TestCase):
    def test_snake_case(self):
        self.assertEqual(to_camel_case("user_id"), "userId")
        self.assertEqual(to_camel_case("first_name_last"), "firstNameLast")

    def test_kebab_case(self):
        self.assertEqual(to_camel_case("user-id"), "userId")

    def test_mixed_separators(self):
        self.assertEqual(to_camel_case("mixed-kebab_snake"), "mixedKebabSnake")

    def test_run_of_separators_counts_as_one(self):
        self.assertEqual(to_camel_case("user__id"), "userId")
        self.assertEqual(to_camel_case("user_-_id"), "userId")

    def test_leading_and_trailing_separators_dropped(self):
        self.assertEqual(to_camel_case("__user_id__"), "userId")
        self.assertEqual(to_camel_case("-user-id-"), "userId")
        self.assertEqual(to_camel_case("_private"), "private")

    def test_first_word_lowered_rest_capitalized(self):
        self.assertEqual(to_camel_case("HTTP_server"), "httpServer")
        self.assertEqual(to_camel_case("user_ID"), "userId")
        self.assertEqual(to_camel_case("SCREAMING_SNAKE"), "screamingSnake")

    def test_no_separator_lowers_only_first_character(self):
        self.assertEqual(to_camel_case("UserId"), "userId")
        self.assertEqual(to_camel_case("HTTPServer"), "hTTPServer")
        self.assertEqual(to_camel_case("already"), "already")
        self.assertEqual(to_camel_case("X"), "x")

    def test_other_characters_are_not_separators(self):
        self.assertEqual(to_camel_case("hello world"), "hello world")
        self.assertEqual(to_camel_case("a.b_c"), "a.bC")

    def test_digits(self):
        self.assertEqual(to_camel_case("parse_url_2"), "parseUrl2")
        self.assertEqual(to_camel_case("user_2fa"), "user2fa")

    def test_non_ascii(self):
        self.assertEqual(to_camel_case("été_chaud"), "étéChaud")

    def test_empty_and_separators_only(self):
        self.assertEqual(to_camel_case(""), "")
        self.assertEqual(to_camel_case("-_-"), "")

    def test_not_inverse_of_to_snake_case(self):
        # ADR 0001, Consequences: the round trip loses the acronym's capitals.
        self.assertEqual(to_camel_case(to_snake_case("HTTPServer")), "httpServer")

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            to_camel_case(None)


class ToKebabCaseTest(unittest.TestCase):
    def test_adr_table_with_dashes(self):
        # Built on to_snake_case: every row of ADR 0001 gives the same words, joined by "-".
        for name, snake in ADR_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), snake.replace("_", "-"))

    def test_examples(self):
        self.assertEqual(to_kebab_case("HTTPServer"), "http-server")
        self.assertEqual(to_kebab_case("camelCase"), "camel-case")
        self.assertEqual(to_kebab_case("PascalCase"), "pascal-case")
        self.assertEqual(to_kebab_case("user_id"), "user-id")
        self.assertEqual(to_kebab_case("parseURL2"), "parse-url2")

    def test_kebab_case_unchanged(self):
        self.assertEqual(to_kebab_case("already-kebab"), "already-kebab")

    def test_matches_to_snake_case(self):
        for name in ("getHTTPResponseCode", "__private_name", "a.b c", "ÉtéChaud"):
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), to_snake_case(name).replace("_", "-"))

    def test_empty_and_separators_only(self):
        self.assertEqual(to_kebab_case(""), "")
        self.assertEqual(to_kebab_case("-_-"), "")

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            to_kebab_case(None)


if __name__ == "__main__":
    unittest.main()
