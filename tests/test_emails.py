"""Tests for textkit.emails: every row of docs/decisions/0003-is-email-accepted-syntax.md."""

import unittest

from textkit.emails import is_email

# The ADR's case table, row for row, in the same order: (input, expected).
_CASES = [
    ("a@b.co", True),
    ("a.b@c.co", True),
    ("a+tag@b.co", True),
    ("A@B.CO", True),
    ("a@b-c.co", True),
    ("a@b.c", True),
    (".a@b.co", False),
    ("a.@b.co", False),
    ("a..b@c.co", False),
    ("a@b", False),
    ("a@b.co.", False),
    ("a@.b.co", False),
    ("a@b..co", False),
    ("a@-b.co", False),
    ("a@b-.co", False),
    ("a@1.2.3.4", False),
    ('"a b"@c.co', False),
    ("a@[1.2.3.4]", False),
    ("ü@b.co", False),
    ("a@b@c.co", False),
    ("@b.co", False),
    ("a@", False),
    ("a", False),
    (" a@b.co", False),
    ("a@b.co\n", False),
    ("", False),
    ("a" * 64 + "@b.co", True),
    ("a" * 65 + "@b.co", False),
    ("a@" + "b" * 63 + ".co", True),
    ("a@" + "b" * 64 + ".co", False),
    ("a@" + ".".join(["b" * 63] * 3) + "." + "c" * 60, True),
    ("a@" + ".".join(["b" * 63] * 3) + "." + "c" * 61, False),
]


class IsEmailTest(unittest.TestCase):
    def test_adr_case_table(self):
        for text, expected in _CASES:
            with self.subTest(text=text):
                self.assertIs(is_email(text), expected)

    def test_length_rows_have_the_stated_lengths(self):
        # The ADR states each construction's length; keep the table honest.
        self.assertEqual(len("a" * 64 + "@b.co"), 69)
        self.assertEqual(len("a@" + ".".join(["b" * 63] * 3) + "." + "c" * 60), 254)
        self.assertEqual(len("a@" + ".".join(["b" * 63] * 3) + "." + "c" * 61), 255)

    def test_kelvin_sign_is_not_k(self):
        # U+212A matches "k" under re.IGNORECASE; the ASCII-only rule must reject it.
        self.assertFalse(is_email("K@b.co"))
        self.assertFalse(is_email("a@K.co"))

    def test_non_ascii_digit_is_rejected(self):
        self.assertFalse(is_email("a@b.١"))

    def test_single_character_argument(self):
        # Phase 3's CLI rule: a one-parameter function is callable with "a".
        self.assertFalse(is_email("a"))

    def test_non_str_raises_type_error(self):
        for value in (None, 1, b"a@b.co"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    is_email(value)


if __name__ == "__main__":
    unittest.main()
