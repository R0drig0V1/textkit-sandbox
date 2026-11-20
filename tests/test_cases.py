"""Tests for textkit.cases. CASES mirrors the table at the end of ADR 0001, row by row;
CAMEL_CASES pins the to_camel_case rules of plan task T1.8."""

import unittest

from textkit.cases import to_camel_case, to_snake_case

# (input, expected) in the order of the table in
# docs/decisions/0001-to-snake-case-word-boundaries.md; keep both in sync.
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
    ("utf8Decoder", "utf8_decoder"),
    ("ABC", "abc"),
    ("SCREAMING_SNAKE", "screaming_snake"),
    ("mixed-Kebab_snakeCase", "mixed_kebab_snake_case"),
    ("__private--name__", "private_name"),
    ("--", ""),
    ("ÉcoleNormale", "école_normale"),
]


class ToSnakeCaseTest(unittest.TestCase):
    def test_adr_table(self):
        for name, expected in CASES:
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), expected)

    def test_idempotent(self):
        for name, _ in CASES:
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)


# (input, expected) for to_camel_case, one or more rows per rule of T1.8.
CAMEL_CASES = [
    # snake_case and kebab-case input
    ("user_id", "userId"),
    ("kebab-case", "kebabCase"),
    ("mixed-kebab_snake", "mixedKebabSnake"),
    # a run of separators counts as one
    ("user__id", "userId"),
    ("a-_-b", "aB"),
    # leading and trailing separators are dropped
    ("__init__", "init"),
    ("-leading-and-trailing-", "leadingAndTrailing"),
    ("_Private", "private"),
    # first word lower-cased, the rest capitalized (str.capitalize)
    ("HTTP_server", "httpServer"),
    ("SCREAMING_SNAKE", "screamingSnake"),
    ("user_ID", "userId"),
    ("parse_url2", "parseUrl2"),
    ("utf8_decoder", "utf8Decoder"),
    ("école_normale", "écoleNormale"),
    # no separator: only the first character lower-cased
    ("PascalCase", "pascalCase"),
    ("camelCase", "camelCase"),
    ("HTTPServer", "hTTPServer"),
    ("word", "word"),
    ("X", "x"),
    ("ÉcoleNormale", "écoleNormale"),
    # empty and separator-only input
    ("", ""),
    ("_", ""),
    ("--__-", ""),
]


class ToCamelCaseTest(unittest.TestCase):
    def test_cases(self):
        for name, expected in CAMEL_CASES:
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), expected)

    def test_camel_case_output_is_a_fixed_point(self):
        # The result never contains a separator, so a second pass only lower-cases its
        # first character, which is already lower-case (or caseless).
        for name, _ in CAMEL_CASES:
            with self.subTest(name=name):
                once = to_camel_case(name)
                self.assertEqual(to_camel_case(once), once)


if __name__ == "__main__":
    unittest.main()
