"""Tests for textkit.cases. ToSnakeCaseTest covers every row of the case table in
docs/decisions/0003-snake-case-capital-runs.md, in the same order."""

import unittest

from textkit.cases import to_snake_case

# The ADR's case table (input -> output). Keep the two in sync.
ADR_CASES = [
    ("HTTPServer", "http_server"),
    ("parseURL2", "parse_url2"),
    ("camelCase", "camel_case"),
    ("PascalCase", "pascal_case"),
    ("kebab-case", "kebab_case"),
    ("already_snake", "already_snake"),
    ("", ""),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("HTTP2Server", "http2_server"),
    ("version2Beta", "version2_beta"),
    ("ABC", "abc"),
    ("iPhone", "i_phone"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("HTTP_server", "http_server"),
    ("kebab--snake__mixed-_case", "kebab_snake_mixed_case"),
    ("-leading_and_trailing-", "leading_and_trailing"),
    ("utf8string", "utf8string"),
    ("ÉtéCase", "étécase"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_case_table(self):
        for name, expected in ADR_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_is_idempotent(self):
        for name, _ in ADR_CASES:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)


if __name__ == "__main__":
    unittest.main()
