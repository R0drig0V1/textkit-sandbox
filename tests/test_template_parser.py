"""Tests for ``textkit.template.parser``: the tree it builds and every syntax error (T3.4).

Every syntax error is checked with its line and column: the position of the opening
delimiter of the offending tag (for a block with no end tag, of its opening tag).
"""

import unittest

from textkit.template import parser
from textkit.template.exceptions import TemplateError, TemplateSyntaxError
from textkit.template.parser import Expression, Filter, For, If, Output, Text


class ParseTreeTest(unittest.TestCase):
    def test_text_and_output(self):
        self.assertEqual(
            parser.parse("Hi {{ name }}!"),
            [Text("Hi "), Output(Expression(("name",)), 1, 4), Text("!")],
        )

    def test_dotted_name_and_filters(self):
        (node,) = parser.parse("{{ user.title | slug|truncate : 20 }}")
        self.assertEqual(
            node.expression,
            Expression(("user", "title"), (Filter("slug"), Filter("truncate", 20))),
        )
        self.assertEqual(node.expression.dotted, "user.title")

    def test_if_else(self):
        (node,) = parser.parse("{% if a %}x{% else %}y{% endif %}")
        self.assertIsInstance(node, If)
        self.assertEqual(node.expression, Expression(("a",)))
        self.assertEqual((node.body, node.orelse), ([Text("x")], [Text("y")]))

    def test_if_without_else_has_empty_orelse(self):
        (node,) = parser.parse("{% if a %}x{% endif %}")
        self.assertEqual((node.body, node.orelse, node.has_else), ([Text("x")], [], False))

    def test_for_with_filters_in_expression(self):
        (node,) = parser.parse("{%for item in data.items%}{{ item }}{%endfor%}")
        self.assertIsInstance(node, For)
        self.assertEqual(node.target, "item")
        self.assertEqual(node.expression, Expression(("data", "items")))
        self.assertEqual(node.body, [Output(Expression(("item",)), 1, 27)])

    def test_blocks_nest(self):
        (outer,) = parser.parse(
            "{% for x in xs %}{% if x %}{% for y in x %}{{ y }}{% endfor %}{% endif %}{% endfor %}"
        )
        (inner_if,) = outer.body
        (inner_for,) = inner_if.body
        self.assertEqual(inner_for.target, "y")
        self.assertEqual(inner_for.body, [Output(Expression(("y",)), 1, 44)])

    def test_tag_words_may_be_separated_by_any_whitespace(self):
        (node,) = parser.parse("{%\tif\na\t%}x{%\nendif\n%}")
        self.assertEqual(node.expression, Expression(("a",)))

    def test_comments_vanish_from_the_tree(self):
        self.assertEqual(parser.parse("a{# x #}b"), [Text("a"), Text("b")])

    def test_unicode_identifiers_are_names(self):
        (node,) = parser.parse("{{ año.ñu }}")
        self.assertEqual(node.expression.names, ("año", "ñu"))


class SyntaxErrorTest(unittest.TestCase):
    def assertSyntaxError(self, template, line, column, fragment):
        with self.assertRaises(TemplateSyntaxError) as caught:
            parser.parse(template)
        error = caught.exception
        self.assertEqual((error.line, error.column), (line, column), error.message)
        self.assertIn(fragment, error.message)
        self.assertEqual(str(error), f"{line}:{column}: {error.message}")

    def test_unterminated_tags(self):
        self.assertSyntaxError("a {{ b", 1, 3, "unterminated '{{'")
        self.assertSyntaxError("a\n {% if b", 2, 2, "unterminated '{%'")
        self.assertSyntaxError("{{ a }}{# b", 1, 8, "unterminated '{#'")

    def test_block_with_no_end_tag_points_at_its_opening_tag(self):
        self.assertSyntaxError("x\n  {% if a %}yes", 2, 3, "'if' has no 'endif'")
        self.assertSyntaxError("{% if a %}{% else %}no", 1, 1, "'if' has no 'endif'")
        self.assertSyntaxError("ab{% for x in y %}{{ x }}", 1, 3, "'for' has no 'endfor'")

    def test_innermost_open_block_is_reported(self):
        self.assertSyntaxError("{% if a %}\n{% for x in y %}", 2, 1, "'for' has no 'endfor'")

    def test_unknown_tag_and_empty_tag(self):
        self.assertSyntaxError("ok {% include x %}", 1, 4, "unknown tag 'include'")
        self.assertSyntaxError("{% elif a %}", 1, 1, "unknown tag 'elif'")
        self.assertSyntaxError("\n\n{%  %}", 3, 1, "empty tag")

    def test_unknown_filter(self):
        self.assertSyntaxError("{{ a | title }}", 1, 1, "unknown filter 'title'")
        self.assertSyntaxError("\r\n {% if a|nope %}{% endif %}", 2, 2, "unknown filter 'nope'")

    def test_bad_filter_arguments(self):
        cases = [
            ("{{ a | truncate:x }}", "integer width"),
            ("{{ a | truncate:-5 }}", "integer width"),
            ("{{ a | truncate:2.5 }}", "integer width"),
            ("{{ a | truncate:٥ }}", "integer width"),  # ARABIC-INDIC DIGIT FIVE
            ("{{ a | truncate: }}", "integer width"),
            ("{{ a | truncate:2 }}", "at least 3"),
            ("{{ a | truncate:0 }}", "at least 3"),
            ("{{ a | truncate }}", "needs a width"),
            ("{{ a | upper:3 }}", "takes no argument"),
        ]
        for template, fragment in cases:
            with self.subTest(template=template):
                self.assertSyntaxError(" " + template, 1, 2, fragment)

    def test_truncate_width_three_is_accepted(self):
        (node,) = parser.parse("{{ a | truncate:3 }}")
        self.assertEqual(node.expression.filters, (Filter("truncate", 3),))

    def test_truncate_width_digit_limit(self):
        # Python 3.11+ (and 3.9.14+) int() rejects strings of more than 4300 digits with a
        # ValueError; the width is capped as text first, so a syntax error comes out instead.
        self.assertSyntaxError(
            "ab{{ a | truncate:" + "9" * 5000 + " }}", 1, 3, "at most 18 digits"
        )
        self.assertSyntaxError("{{ a | truncate:" + "1" * 19 + " }}", 1, 1, "at most 18 digits")
        (node,) = parser.parse("{{ a | truncate:" + "9" * 18 + " }}")
        self.assertEqual(node.expression.filters, (Filter("truncate", 10**18 - 1),))

    def test_truncate_width_leading_zeros_do_not_count(self):
        (node,) = parser.parse("{{ a | truncate:" + "0" * 5000 + "12 }}")
        self.assertEqual(node.expression.filters, (Filter("truncate", 12),))
        self.assertSyntaxError("{{ a | truncate:" + "0" * 5000 + " }}", 1, 1, "at least 3")

    def test_closing_tags_without_their_opening_tag(self):
        self.assertSyntaxError("a{% else %}", 1, 2, "'else' without a matching 'if'")
        self.assertSyntaxError("ab{% endif %}", 1, 3, "'endif' without a matching 'if'")
        self.assertSyntaxError("\nabc{% endfor %}", 2, 4, "'endfor' without a matching 'for'")

    def test_closing_tag_of_the_wrong_block(self):
        self.assertSyntaxError(
            "{% if a %}{% endfor %}", 1, 11, "'endfor' without a matching 'for'"
        )
        self.assertSyntaxError(
            "{% for x in y %}{% else %}{% endfor %}", 1, 17, "'else' without a matching 'if'"
        )

    def test_second_else_in_one_if(self):
        self.assertSyntaxError(
            "{% if a %}1{% else %}2{% else %}3{% endif %}", 1, 23, "second 'else'"
        )

    def test_end_tags_take_no_argument(self):
        self.assertSyntaxError("{% if a %}{% endif a %}", 1, 11, "takes nothing after it")

    def test_malformed_expressions(self):
        cases = [
            ("{{ }}", "missing name"),
            ("{{ | upper }}", "missing name"),
            ("{{ a b }}", "invalid name"),
            ("{{ a..b }}", "invalid name"),
            ("{{ a.0 }}", "invalid name"),
            ("{{ a | }}", "missing filter name"),
            ("{% if %}{% endif %}", "'if' needs an expression"),
        ]
        for template, fragment in cases:
            with self.subTest(template=template):
                self.assertSyntaxError(template, 1, 1, fragment)

    def test_malformed_for(self):
        self.assertSyntaxError("{% for x %}{% endfor %}", 1, 1, "malformed 'for'")
        self.assertSyntaxError("{% for a.b in c %}{% endfor %}", 1, 1, "invalid loop variable")
        self.assertSyntaxError("{% for loop in c %}{% endfor %}", 1, 1, "'loop' cannot be")

    def test_nesting_limit(self):
        ok = "{% if a %}" * parser.MAX_DEPTH + "{% endif %}" * parser.MAX_DEPTH
        self.assertEqual(len(parser.parse(ok)), 1)
        too_deep = "{% if a %}" * (parser.MAX_DEPTH + 1)
        self.assertSyntaxError(too_deep, 1, 10 * parser.MAX_DEPTH + 1, "nested deeper")

    def test_syntax_error_is_a_template_error_and_a_value_error(self):
        # Base class per the phase 3 rule "Errors" (before textkit.errors exists).
        self.assertTrue(issubclass(TemplateSyntaxError, TemplateError))
        self.assertTrue(issubclass(TemplateError, ValueError))


if __name__ == "__main__":
    unittest.main()
