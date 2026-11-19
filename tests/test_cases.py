"""Tests for textkit.cases.

`CASES` is the table of cases at the end of the ADR "How `to_snake_case` splits runs of
capitals" (docs/decisions/NNNN-snake-case-capital-runs.md); every row is tested, and a
sync test keeps the ADR table and `CASES` identical. `CAMEL_CASES` pins the behaviour of
`to_camel_case` described in plan task T1.8 and its docstring. `ToKebabCaseTest` checks that
`to_kebab_case` (plan task T2.3) is `to_snake_case` joined with `-`, on every row of `CASES`.
"""

import ast
import pathlib
import re
import unittest

from textkit.cases import to_camel_case, to_kebab_case, to_snake_case

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# (input, output), in the order of the ADR table.
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
    ("ABC", "abc"),
    ("A", "a"),
    ("ipv4Address", "ipv4_address"),
    ("version2Beta", "version2_beta"),
    ("PDFs", "pd_fs"),
    ("Already_Snake", "already_snake"),
    ("kebab--case", "kebab_case"),
    ("-leading-and-trailing-", "leading_and_trailing"),
    ("_private", "private"),
    ("mixed-kebab_snakeCase", "mixed_kebab_snake_case"),
    ("---", ""),
    ("ÉcoleNormale", "école_normale"),
]


def _adr_cases() -> list[tuple[str, str]]:
    """Read the (input, output) rows of the case table in the ADR on capital runs.

    The ADR is found by its title, not its number, because the integrator may renumber it.
    """
    (adr,) = (_ROOT / "docs" / "decisions").glob("*-snake-case-capital-runs.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| `(.*)` \|$", table, re.M)
    return [(ast.literal_eval(i), ast.literal_eval(o)) for i, o in rows]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_table(self):
        for name, expected in CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), CASES)

    def test_required_rows_present(self):
        # The minimum rows plan task T1.7 asks the ADR table for.
        inputs = {name for name, _ in CASES}
        required = {"HTTPServer", "parseURL2", "camelCase", "PascalCase", "kebab-case",
                    "already_snake", ""}
        self.assertLessEqual(required, inputs)

    def test_idempotent(self):
        for _, expected in CASES:
            with self.subTest(name=expected):
                self.assertEqual(to_snake_case(expected), expected)

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_snake_case(None)
        with self.assertRaises(TypeError):
            to_snake_case(b"camelCase")


# (input, output) for to_camel_case: the plan's examples first, then the edge cases.
CAMEL_CASES = [
    ("user_id", "userId"),
    ("HTTP_server", "httpServer"),
    ("kebab-case", "kebabCase"),
    ("kebab--case", "kebabCase"),
    ("__leading_and_trailing__", "leadingAndTrailing"),
    ("-a--b-", "aB"),
    ("mixed-kebab_snake", "mixedKebabSnake"),
    ("user_ID", "userId"),
    ("SCREAMING_SNAKE_CASE", "screamingSnakeCase"),
    ("ipv4_address", "ipv4Address"),
    ("version_2", "version2"),
    ("_private", "private"),
    ("_PascalCase", "pascalcase"),
    ("École_normale", "écoleNormale"),
    ("PascalCase", "pascalCase"),
    ("HTTPServer", "hTTPServer"),
    ("camelCase", "camelCase"),
    ("X", "x"),
    ("x", "x"),
    ("", ""),
    ("---", ""),
]


class ToCamelCaseTest(unittest.TestCase):
    def test_cases(self):
        for name, expected in CAMEL_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_no_separator_changes_only_first_character(self):
        for name in ("HTTPServer", "already camel", "Ünïcode", "9Lives"):
            with self.subTest(name=name):
                result = to_camel_case(name)
                self.assertEqual(result[1:], name[1:])
                self.assertEqual(result[:1], name[:1].lower())

    def test_idempotent(self):
        for _, expected in CAMEL_CASES:
            with self.subTest(name=expected):
                self.assertEqual(to_camel_case(expected), expected)

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_camel_case(None)
        with self.assertRaises(TypeError):
            to_camel_case(b"user_id")


class ToKebabCaseTest(unittest.TestCase):
    def test_cases(self):
        for name, expected in [
            ("HTTPServer", "http-server"),
            ("parseURL2", "parse-url2"),
            ("camelCase", "camel-case"),
            ("PascalCase", "pascal-case"),
            ("already_snake", "already-snake"),
            ("kebab-case", "kebab-case"),
            ("-a--b-", "a-b"),
            ("mixed-kebab_snakeCase", "mixed-kebab-snake-case"),
            ("PDFs", "pd-fs"),
            ("ÉcoleNormale", "école-normale"),
            ("", ""),
            ("---", ""),
        ]:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), expected)

    def test_matches_snake_case_on_every_adr_row(self):
        for name, snake in CASES:
            with self.subTest(name=name):
                self.assertEqual(to_kebab_case(name), snake.replace("_", "-"))
                self.assertNotIn("_", to_kebab_case(name))

    def test_idempotent(self):
        for name, _ in CASES:
            kebab = to_kebab_case(name)
            with self.subTest(name=kebab):
                self.assertEqual(to_kebab_case(kebab), kebab)

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_kebab_case(None)
        with self.assertRaises(TypeError):
            to_kebab_case(b"camelCase")


if __name__ == "__main__":
    unittest.main()
