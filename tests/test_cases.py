"""Tests for textkit.cases.

`CASES` is the table of cases at the end of the ADR "How `to_snake_case` splits runs of
capitals" (docs/decisions/NNNN-snake-case-capital-runs.md); every row is tested, and a
sync test keeps the ADR table and `CASES` identical.
"""

import ast
import pathlib
import re
import unittest

from textkit.cases import to_snake_case

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


if __name__ == "__main__":
    unittest.main()
