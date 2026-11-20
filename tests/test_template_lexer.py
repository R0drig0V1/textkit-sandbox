"""Tests for textkit/template/lexer.py, the tokenizer of the template engine (plan task T3.4).

Positions are checked everywhere they appear: line and column from 1, columns in code
points, a new line only after ``"\\n"`` (``docs/template.md``).
"""

import unittest

from textkit.template.errors import TemplateSyntaxError
from textkit.template.lexer import BLOCK, OUTPUT, TEXT, Token, tokenize


class TokenizeTest(unittest.TestCase):
    def assertSyntaxErrorAt(self, template: str, line: int, column: int) -> None:
        with self.assertRaises(TemplateSyntaxError) as caught:
            tokenize(template)
        self.assertEqual((caught.exception.line, caught.exception.column), (line, column))

    def test_empty_template_gives_no_tokens(self):
        self.assertEqual(tokenize(""), [])

    def test_text_without_tags_is_one_token_exactly_as_written(self):
        text = "a { b } c }} d %} e #}\r\nf\rg"
        self.assertEqual(tokenize(text), [Token(TEXT, text, 1, 1)])

    def test_output_tag_value_is_stripped_and_spaces_are_optional(self):
        self.assertEqual(tokenize("{{x}}"), [Token(OUTPUT, "x", 1, 1)])
        self.assertEqual(tokenize("{{  x | upper \t}}"), [Token(OUTPUT, "x | upper", 1, 1)])

    def test_block_tag_and_surrounding_text(self):
        self.assertEqual(
            tokenize("a{%if x%}b"),
            [Token(TEXT, "a", 1, 1), Token(BLOCK, "if x", 1, 2), Token(TEXT, "b", 1, 10)],
        )

    def test_comments_produce_no_token(self):
        self.assertEqual(
            tokenize("a{# note {{ x }} {% if %} #}b"),
            [Token(TEXT, "a", 1, 1), Token(TEXT, "b", 1, 29)],
        )
        self.assertEqual(tokenize("{##}"), [])

    def test_a_tag_ends_at_the_first_closer(self):
        self.assertEqual(
            tokenize("{{ a }} b }}"), [Token(OUTPUT, "a", 1, 1), Token(TEXT, " b }}", 1, 8)]
        )
        # A different closer does not end the tag.
        self.assertEqual(tokenize("{{ a %} }}"), [Token(OUTPUT, "a %}", 1, 1)])

    def test_positions_across_lines(self):
        self.assertEqual(
            tokenize("ab\n  {{ x }}\n{% endif %}"),
            [
                Token(TEXT, "ab\n  ", 1, 1),
                Token(OUTPUT, "x", 2, 3),
                Token(TEXT, "\n", 2, 10),
                Token(BLOCK, "endif", 3, 1),
            ],
        )

    def test_a_tag_spanning_lines_moves_the_position_of_what_follows(self):
        self.assertEqual(
            tokenize("{{\n x \n}}z"), [Token(OUTPUT, "x", 1, 1), Token(TEXT, "z", 3, 3)]
        )

    def test_carriage_return_is_a_column_not_a_line(self):
        self.assertEqual(tokenize("a\r{{ x }}")[1], Token(OUTPUT, "x", 1, 3))
        self.assertEqual(tokenize("a\r\n{{ x }}")[1], Token(OUTPUT, "x", 2, 1))

    def test_columns_count_code_points(self):
        # One code point outside the BMP, then a base letter plus a combining mark (NFD).
        self.assertEqual(tokenize("\U0001F600{{ x }}")[1], Token(OUTPUT, "x", 1, 2))
        self.assertEqual(tokenize("café {{ x }}")[1], Token(OUTPUT, "x", 1, 7))

    def test_unterminated_output_tag(self):
        self.assertSyntaxErrorAt("ok\n  {{ name ", 2, 3)

    def test_unterminated_block_tag(self):
        self.assertSyntaxErrorAt("{{ a }}{% if x", 1, 8)
        # "{%}" is not closed by its own "%}".
        self.assertSyntaxErrorAt("{%}", 1, 1)

    def test_unterminated_comment(self):
        self.assertSyntaxErrorAt("a\r\nb {# never closed }}", 2, 3)

    def test_unterminated_error_names_the_delimiters(self):
        with self.assertRaises(TemplateSyntaxError) as caught:
            tokenize("{{ x")
        self.assertEqual(caught.exception.message, "'{{' is never closed with '}}'")
        self.assertEqual(str(caught.exception), "1:1: '{{' is never closed with '}}'")


if __name__ == "__main__":
    unittest.main()
