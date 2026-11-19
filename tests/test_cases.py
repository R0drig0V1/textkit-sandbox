"""Tests for textkit.cases: to_snake_case, the examples of ADR 0002, and to_camel_case."""

import pathlib
import re
import unicodedata
import unittest

from textkit.cases import to_camel_case, to_snake_case

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
            for form in ("NFC", "NFD"):
                with self.subTest(src=src, form=form):
                    self.assertEqual(
                        to_snake_case(unicodedata.normalize(form, src)),
                        unicodedata.normalize(form, expected),
                    )


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

    def test_decomposed_marks_continue_the_word(self):
        # Written decomposed on purpose: "e" + U+0301 COMBINING ACUTE ACCENT.
        self.check([
            ("re\u0301sume\u0301File", "re\u0301sume\u0301_file"),
            ("cafe\u0301AuLait", "cafe\u0301_au_lait"),
            # The mark sits between capitals: still one run of capitals.
            ("E\u0301TE\u0301Fini", "e\u0301te\u0301_fini"),
            # The mark sits between the capital and its lower-case letter.
            ("XMLE\u0301tude", "xml_e\u0301tude"),
            ("user_e\u0301t\u00e9", "user_e\u0301t\u00e9"),  # mixed forms, unchanged
        ])

    def test_nfc_and_nfd_give_the_same_words(self):
        for name in ("résuméFile", "ÉTÉFini", "XMLÉtude", "naïve-Über", "ÅngströmUnit",
                     "हिन्दीText"):
            with self.subTest(name=name):
                nfc = to_snake_case(unicodedata.normalize("NFC", name))
                nfd = to_snake_case(unicodedata.normalize("NFD", name))
                self.assertEqual(unicodedata.normalize("NFC", nfd), nfc)

    def test_mark_without_a_word_is_dropped(self):
        self.check([
            ("\u0301abc", "abc"),
            ("a-\u0301b", "a_b"),
            ("\u0301", ""),
            ("a_\u0301\u0301_b", "a_b"),
        ])

    def test_non_str_raises_type_error(self):
        for bad in (None, 42, b"camelCase", ["a", "B"]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    to_snake_case(bad)  # type: ignore[arg-type]


class ToCamelCaseTest(unittest.TestCase):
    def check(self, cases):
        for src, expected in cases:
            with self.subTest(src=src):
                self.assertEqual(to_camel_case(src), expected)

    def test_snake_and_kebab(self):
        self.check([
            ("user_id", "userId"),
            ("kebab-case", "kebabCase"),
            ("get_http_response_code", "getHttpResponseCode"),
            ("mixed_kebab-and snake", "mixedKebabAndSnake"),
            ("user", "user"),
            ("a_b", "aB"),
        ])

    def test_separators_at_ends_and_repeated(self):
        self.check([
            ("_private", "private"),
            ("__user__id_", "userId"),
            ("user--id", "userId"),
            ("-user-id-", "userId"),
            ("user name.v2", "userNameV2"),
            ("-_- ", ""),
        ])

    def test_digits(self):
        self.check([
            ("version_2_beta", "version2Beta"),
            ("utf8_decode", "utf8Decode"),
            ("user_2fa", "user2fa"),
            ("2fa_code", "2faCode"),
            ("base64", "base64"),
        ])

    def test_digit_words_do_not_round_trip(self):
        # Documented: a digits-only word joins the previous one.
        self.assertEqual(to_snake_case(to_camel_case("version_2_beta")), "version2_beta")

    def test_upper_case_input(self):
        self.check([("USER_ID", "userId"), ("SCREAMING-KEBAB", "screamingKebab"),
                    ("ABC", "abc")])

    def test_camel_case_input_is_unchanged(self):
        for name in ("userId", "parseUrl", "getHttpResponseCode", "utf8Decode", "a"):
            with self.subTest(name=name):
                self.assertEqual(to_camel_case(name), name)

    def test_pascal_case_and_acronyms_are_split_first(self):
        self.check([
            ("UserId", "userId"),
            ("PascalCase", "pascalCase"),
            ("HTTPServer", "httpServer"),
            ("parseURL", "parseUrl"),
            ("my-HTTPServer", "myHttpServer"),
            ("IOError", "ioError"),
        ])

    def test_idempotent(self):
        for name in ("user_id", "HTTPServer", "version_2_beta", "naïve-über", "USER_ID"):
            with self.subTest(name=name):
                once = to_camel_case(name)
                self.assertEqual(to_camel_case(once), once)

    def test_non_ascii_letters(self):
        self.check([
            ("naïve-über", "naïveÜber"),
            ("été_fini", "étéFini"),
            ("straße_name", "straßeName"),
            ("日本_語", "日本語"),  # caseless words are joined as they are
        ])

    def test_decomposed_marks_stay_with_their_letter(self):
        # Written decomposed on purpose: "e" + U+0301 COMBINING ACUTE ACCENT.
        self.check([
            ("user_e\u0301tude", "userE\u0301tude"),
            ("re\u0301sume\u0301_file", "re\u0301sume\u0301File"),
            ("a-\u0301b", "aB"),  # a mark with no word to attach to is dropped
        ])

    def test_nfc_and_nfd_give_the_same_result(self):
        for name in ("naïve-über", "été_fini", "user_étude", "ÉTÉ_FINI", "XMLÉtude",
                     "ÅngströmUnit"):
            with self.subTest(name=name):
                nfc = to_camel_case(unicodedata.normalize("NFC", name))
                nfd = to_camel_case(unicodedata.normalize("NFD", name))
                self.assertEqual(unicodedata.normalize("NFC", nfd), nfc)
                # The result keeps the input's form.
                self.assertEqual(nfd, unicodedata.normalize("NFD", nfd))

    def test_empty(self):
        self.assertEqual(to_camel_case(""), "")

    def test_non_str_raises_type_error(self):
        for bad in (None, 42, b"user_id", ["user", "id"]):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(TypeError, "to_camel_case"):
                    to_camel_case(bad)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
