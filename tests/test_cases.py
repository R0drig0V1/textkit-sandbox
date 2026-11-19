"""Tests for textkit.cases. One TestCase class per public function, in module order."""

import ast
import pathlib
import re
import unittest

from textkit.cases import to_snake_case

# The table of cases at the end of ADR "to-snake-case-capital-runs" (docs/decisions/), in the
# same order. test_adr_table_matches keeps the two in sync.
SNAKE_CASES = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("userID", "user_id"),
    ("IOError", "io_error"),
    ("HTTP", "http"),
    ("HTTP2Server", "http2_server"),
    ("utf8Encode", "utf8_encode"),
    ("parse2URL", "parse2_url"),
    ("Kebab-Case", "kebab_case"),
    ("mixed-camelCase", "mixed_camel_case"),
    ("HTTP_Server", "http_server"),
    ("a--b__c", "a_b_c"),
    ("__private__", "private"),
    ("--", ""),
]

REPO = pathlib.Path(__file__).resolve().parent.parent


def _adr_cases() -> list[tuple[str, str]]:
    """Read the (input, output) rows of the ADR's case table, whatever its number."""
    # Matched by title, not number: the integrator may renumber the ADR at merge.
    (adr,) = (REPO / "docs" / "decisions").glob("*-to-snake-case-capital-runs.md")
    rows = re.findall(r'^\| `(".*?")` \| `(".*?")` \|$', adr.read_text(), re.M)
    return [(ast.literal_eval(i), ast.literal_eval(o)) for i, o in rows]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_cases(self):
        for name, expected in SNAKE_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_adr_table_matches(self):
        self.assertEqual(_adr_cases(), SNAKE_CASES)

    def test_idempotent(self):
        for name, _ in SNAKE_CASES:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)

    def test_other_characters_kept_and_lowered(self):
        self.assertEqual(to_snake_case("ÉcoleName"), "école_name")
        self.assertEqual(to_snake_case("a.bC"), "a.b_c")

    def test_non_str_raises_type_error(self):
        for value in (None, 42, b"camelCase"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_snake_case(value)


if __name__ == "__main__":
    unittest.main()
