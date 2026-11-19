"""Tests for textkit.emails, one TestCase class per public function.

IsEmailTest tests every row of the case table that ends the email ADR
(docs/decisions/*-what-is-an-email-address.md) and checks that the table and CASES stay
identical, so neither can drift from the other. The long rows are built here with the
construction the ADR states next to them, so the comparison also checks each construction.
"""

import ast
import pathlib
import re
import unittest

from textkit.emails import is_email

_THREE_63 = ".".join(["b" * 63] * 3)

# Mirror of the case table in docs/decisions/*-what-is-an-email-address.md: (input, result).
CASES = [
    ("a@b.co", True),
    ("a.b@c.co", True),
    ("A+tag_1-x@Sub-1.Example.COM", True),
    ("!#$%&'*+/=?^_{}~-@b.co", True),
    ("a@b.c0", True),
    (".a@b.co", False),
    ("a.@b.co", False),
    ("a..b@c.co", False),
    ("a@b", False),
    ("a@b.co.", False),
    ("a@.b.co", False),
    ("a@b..co", False),
    ("a@-b.co", False),
    ("a@b-.co", False),
    ("a@b_c.co", False),
    ("a@1.2.3.4", False),
    ("a@b.123", False),
    ('"a b"@c.co', False),
    ("a@[1.2.3.4]", False),
    ("ü@b.co", False),
    ("a@bü.co", False),
    ("a@b@c.co", False),
    ("a.b.co", False),
    ("@b.co", False),
    ("a@", False),
    (" a@b.co", False),
    ("a@b.co\n", False),
    ("a b@c.co", False),
    ("", False),
    ("a" * 64 + "@b.co", True),
    ("a" * 65 + "@b.co", False),
    ("a@" + "b" * 63 + ".co", True),
    ("a@" + "b" * 64 + ".co", False),
    ("a@" + _THREE_63 + "." + "c" * 60, True),
    ("a@" + _THREE_63 + "." + "c" * 61, False),
]

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _adr_cases() -> list:
    """Parse the case table of the email ADR. Glob on the slug: the number may change at merge."""
    (adr,) = sorted((_ROOT / "docs" / "decisions").glob("*-what-is-an-email-address.md"))
    rows = re.findall(r"^\| `(.*)` \| (True|False) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), result == "True") for literal, result in rows]


class IsEmailTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in CASES:
            with self.subTest(text=text):
                self.assertIs(is_email(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), CASES)

    def test_length_rows_sit_on_the_limits(self):
        # The ADR names these rows by length; pin the lengths so a typo cannot move a row
        # off the boundary it is meant to test.
        self.assertEqual(len("a" * 64 + "@b.co") - len("@b.co"), 64)
        self.assertEqual(len("a@" + _THREE_63 + "." + "c" * 60), 254)
        self.assertEqual(len("a@" + _THREE_63 + "." + "c" * 61), 255)

    def test_backtick_and_pipe_are_atext(self):
        # Kept out of the ADR table: a Markdown code span in a table cell cannot hold them.
        self.assertIs(is_email("a`b@c.co"), True)
        self.assertIs(is_email("a|b@c.co"), True)

    def test_whitespace_and_control_characters_are_rejected(self):
        for text in ("a@b.co ", "a\t@b.co", "a@b.co\r\n", "a@b .co", "a\x00@b.co"):
            with self.subTest(text=text):
                self.assertIs(is_email(text), False)

    def test_non_ascii_lookalikes_are_rejected(self):
        # Fullwidth "@", Kelvin sign "K", Arabic-Indic digit: rejected because every rule
        # uses explicit ASCII sets, not \w or str.isalnum.
        for text in ("a＠b.co", "K@b.co", "a@b.c١", "a@b.co "):
            with self.subTest(text=text):
                self.assertIs(is_email(text), False)

    def test_any_str_returns_a_bool(self):
        # Phase-3 rule: called by the CLI with "a", it must not raise anything but
        # ValueError, KeyError or TypeError; is_email returns False for any str.
        self.assertIs(is_email("a"), False)

    def test_rejects_non_str(self):
        for value in (None, 42, b"a@b.co", ["a@b.co"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    is_email(value)


if __name__ == "__main__":
    unittest.main()
