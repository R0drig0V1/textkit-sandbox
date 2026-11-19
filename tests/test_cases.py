"""Tests for textkit.cases: to_snake_case and the examples of ADR 0002."""

import pathlib
import re
import unittest

from textkit.cases import to_snake_case

ADR = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions" / (
    "0002-snake-case-word-boundaries.md"
)


def _adr_examples():
    """(input, output) pairs from the ADR's example table; `(empty)` stands for ""."""
    pairs = []
    for line in ADR.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (`[^`]*`|\(empty\)) \| (`[^`]*`|\(empty\)) \|", line)
        if m:
            src, out = (cell.strip("`") if cell != "(empty)" else "" for cell in m.groups())
            pairs.append((src, out))
    return pairs


class AdrExamplesTest(unittest.TestCase):
    def test_every_adr_example(self):
        examples = _adr_examples()
        # Guard against the table parser silently matching nothing.
        self.assertGreaterEqual(len(examples), 20)
        for src, expected in examples:
            with self.subTest(src=src):
                self.assertEqual(to_snake_case(src), expected)


class ToSnakeCaseTest(unittest.TestCase):
    def check(self, cases):
        for src, expected in cases:
            with self.subTest(src=src):
                self.assertEqual(to_snake_case(src), expected)

    def test_camel_and_pascal(self):
        self.check([("parseUrl", "parse_url"), ("PascalCase", "pascal_case"), ("aB", "a_b")])

    def test_runs_of_capitals(self):
        self.check([
            ("HTTPServer", "http_server"),
            ("getHTTPResponseCode", "get_http_response_code"),
            ("IOError", "io_error"),
            ("parseURL", "parse_url"),
            ("ABC", "abc"),
            ("ABC2def", "abc2def"),
        ])

    def test_digits_stay_with_previous_word(self):
        self.check([
            ("parseURL2", "parse_url2"),
            ("URL2Path", "url2_path"),
            ("HTTP2Server", "http2_server"),
            ("utf8Decode", "utf8_decode"),
            ("base64", "base64"),
            ("version2beta", "version2beta"),
            ("2fa", "2fa"),
        ])

    def test_separators(self):
        self.check([
            ("kebab-case", "kebab_case"),
            ("my-HTTPServer", "my_http_server"),
            ("SCREAMING_SNAKE", "screaming_snake"),
            ("user--id", "user_id"),
            ("_private", "private"),
            ("__init__", "init"),
            ("user name.v2", "user_name_v2"),
            ("-_- ", ""),
        ])

    def test_already_snake_is_unchanged(self):
        for name in ("user_id", "a", "http_server_v2", "already_snake_case"):
            with self.subTest(name=name):
                self.assertEqual(to_snake_case(name), name)

    def test_idempotent(self):
        for name in ("HTTPServer", "parseURL2", "my-HTTPServer", "utf8Decode"):
            with self.subTest(name=name):
                once = to_snake_case(name)
                self.assertEqual(to_snake_case(once), once)

    def test_empty(self):
        self.assertEqual(to_snake_case(""), "")

    def test_non_ascii_letters(self):
        self.check([("caféAuLait", "café_au_lait"), ("ÉtéFini", "été_fini")])

    def test_non_str_raises_type_error(self):
        for bad in (None, 42, b"camelCase", ["a", "B"]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    to_snake_case(bad)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
