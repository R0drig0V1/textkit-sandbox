"""Tests for ``textkit.template.lexer``: tokens, comments, positions and unterminated tags (T3.4)."""

import unittest

from textkit.template import lexer
from textkit.template.exceptions import TemplateSyntaxError
from textkit.template.lexer import BLOCK, TEXT, VAR, Token


class TokenizeTest(unittest.TestCase):
    def test_plain_text_is_one_token(self):
        self.assertEqual(lexer.tokenize("hello"), [Token(TEXT, "hello", 1, 1)])

    def test_empty_template_has_no_tokens(self):
        self.assertEqual(lexer.tokenize(""), [])

    def test_kinds_and_stripped_content(self):
        self.assertEqual(
            lexer.tokenize("a{{ x }}b{%  if y %}"),
            [
                Token(TEXT, "a", 1, 1),
                Token(VAR, "x", 1, 2),
                Token(TEXT, "b", 1, 9),
                Token(BLOCK, "if y", 1, 10),
            ],
        )

    def test_spaces_inside_delimiters_are_optional(self):
        self.assertEqual(lexer.tokenize("{{x}}"), lexer.tokenize("{{ x }}"))
        self.assertEqual(lexer.tokenize("{%if x%}")[0].value, "if x")

    def test_comments_produce_no_token(self):
        self.assertEqual(
            lexer.tokenize("a{# {{ not a tag }} #}b"),
            [Token(TEXT, "a", 1, 1), Token(TEXT, "b", 1, 23)],
        )

    def test_lone_braces_are_text(self):
        self.assertEqual(lexer.tokenize("{ x } {x} }}"), [Token(TEXT, "{ x } {x} }}", 1, 1)])

    def test_tag_ends_at_first_closer_of_its_kind(self):
        # "%}" does not close an output tag; the first "}}" does.
        self.assertEqual(lexer.tokenize("{{ a %} }}"), [Token(VAR, "a %}", 1, 1)])

    def test_crlf_text_is_kept_as_is(self):
        tokens = lexer.tokenize("a\r\n{{ x }}\r\n")
        self.assertEqual(tokens[0], Token(TEXT, "a\r\n", 1, 1))
        self.assertEqual(tokens[1], Token(VAR, "x", 2, 1))
        self.assertEqual(tokens[2], Token(TEXT, "\r\n", 2, 8))

    def test_lone_cr_is_a_column_not_a_line(self):
        self.assertEqual(lexer.tokenize("a\r{{ x }}")[1], Token(VAR, "x", 1, 3))

    def test_columns_count_code_points(self):
        # U+1F600 is one code point (two UTF-16 units, four UTF-8 bytes): one column.
        self.assertEqual(lexer.tokenize("\U0001F600{{ x }}")[1].column, 2)
        self.assertEqual(lexer.tokenize("é{{ x }}")[1].column, 3)

    def test_multiline_tag_starts_where_its_delimiter_is(self):
        tokens = lexer.tokenize("ab\ncd{{\n x \n}}e")
        self.assertEqual(tokens[1], Token(VAR, "x", 2, 3))
        self.assertEqual(tokens[2], Token(TEXT, "e", 4, 3))


class UnterminatedTest(unittest.TestCase):
    def test_each_opener_reports_its_own_position(self):
        cases = [
            ("ab{{ x", "{{", (1, 3)),
            ("a\nb{% if x", "{%", (2, 2)),
            ("a\n\n  {# note", "{#", (3, 3)),
        ]
        for template, opener, (line, column) in cases:
            with self.subTest(template=template):
                with self.assertRaises(TemplateSyntaxError) as caught:
                    lexer.tokenize(template)
                self.assertEqual((caught.exception.line, caught.exception.column), (line, column))
                self.assertIn(repr(opener), caught.exception.message)

    def test_a_closer_of_another_kind_does_not_terminate(self):
        with self.assertRaises(TemplateSyntaxError) as caught:
            lexer.tokenize("x {# note }} %}")
        self.assertEqual((caught.exception.line, caught.exception.column), (1, 3))

    def test_opener_overlapping_its_closer_is_unterminated(self):
        # "{#}" is not an empty comment: the closer must start after the opener.
        with self.assertRaises(TemplateSyntaxError):
            lexer.tokenize("{#}")


class PositionTest(unittest.TestCase):
    def test_positions(self):
        text = "ab\r\ncd\n\nx"
        self.assertEqual(lexer.position(text, 0), (1, 1))
        self.assertEqual(lexer.position(text, 2), (1, 3))  # the "\r"
        self.assertEqual(lexer.position(text, 4), (2, 1))
        self.assertEqual(lexer.position(text, 7), (3, 1))
        self.assertEqual(lexer.position(text, len(text)), (4, 2))

    def test_offset_outside_the_template_raises(self):
        for offset in (-1, 4):
            with self.subTest(offset=offset):
                with self.assertRaises(IndexError):
                    lexer.position("abc", offset)


if __name__ == "__main__":
    unittest.main()
