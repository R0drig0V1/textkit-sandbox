"""Tests for textkit/template/parser.py, the parser of the template engine (plan task T3.4).

Every syntax error the parser raises is checked with its line and column: the position of
the opening delimiter of the tag at fault, or of a block's opening tag when it has no end.
"""

import unittest

from textkit.template.errors import TemplateSyntaxError
from textkit.template.lexer import OUTPUT, Token
from textkit.template.parser import (
    Expr,
    Filter,
    For,
    If,
    Output,
    Text,
    parse,
    parse_expr,
)

# parse_expr only uses a token for the position of its errors.
_AT = Token(OUTPUT, "", 4, 9)


def _expr(*names: str, filters: tuple = ()) -> Expr:
    return Expr(tuple(names), tuple(filters))


class ParseExprTest(unittest.TestCase):
    def assertExprErrorAtToken(self, source: str) -> TemplateSyntaxError:
        with self.assertRaises(TemplateSyntaxError) as caught:
            parse_expr(source, _AT)
        self.assertEqual((caught.exception.line, caught.exception.column), (4, 9))
        return caught.exception

    def test_dotted_names(self):
        self.assertEqual(parse_expr("x", _AT), _expr("x"))
        self.assertEqual(parse_expr("user.address.city", _AT), _expr("user", "address", "city"))
        self.assertEqual(parse_expr("café", _AT), _expr("café"))

    def test_filters_in_order_with_optional_spaces(self):
        expected = _expr(
            "title", filters=(Filter("slug", None), Filter("truncate", 20))
        )
        self.assertEqual(parse_expr("title | slug | truncate:20", _AT), expected)
        self.assertEqual(parse_expr("title|slug|truncate:20", _AT), expected)
        self.assertEqual(parse_expr("title |  slug|truncate : 20 ", _AT), expected)

    def test_every_filter_of_the_table_is_accepted(self):
        for name in ("slug", "snake", "camel", "kebab", "squeeze", "strip_accents", "upper",
                     "lower"):
            with self.subTest(name=name):
                self.assertEqual(
                    parse_expr(f"x | {name}", _AT), _expr("x", filters=(Filter(name, None),))
                )
        self.assertEqual(
            parse_expr("x | truncate:3", _AT), _expr("x", filters=(Filter("truncate", 3),))
        )

    def test_invalid_names(self):
        for source in ("", "  ", "a..b", ".a", "a.", "1x", "a b", "a-b", "'a'", "a.0"):
            with self.subTest(source=source):
                self.assertExprErrorAtToken(source)

    def test_unknown_filter(self):
        error = self.assertExprErrorAtToken("x | title")
        self.assertIn("unknown filter 'title'", error.message)

    def test_empty_filter(self):
        for source in ("x |", "x || upper", "x | :3"):
            with self.subTest(source=source):
                self.assertExprErrorAtToken(source)

    def test_truncate_without_a_width(self):
        for source in ("x | truncate", "x | truncate:", "x | truncate :  "):
            with self.subTest(source=source):
                error = self.assertExprErrorAtToken(source)
                self.assertIn("needs a width", error.message)

    def test_truncate_with_a_non_integer_width(self):
        for source in ("x | truncate:x", "x | truncate:2.5", "x | truncate:1_000",
                       "x | truncate:٥", "x | truncate:5:6"):
            with self.subTest(source=source):
                error = self.assertExprErrorAtToken(source)
                self.assertIn("must be an integer", error.message)

    def test_truncate_with_a_width_below_three(self):
        for source in ("x | truncate:2", "x | truncate:0", "x | truncate:-5"):
            with self.subTest(source=source):
                error = self.assertExprErrorAtToken(source)
                self.assertIn("at least 3", error.message)
        self.assertEqual(parse_expr("x|truncate:+3", _AT).filters, (Filter("truncate", 3),))

    def test_argument_to_a_filter_that_takes_none(self):
        error = self.assertExprErrorAtToken("x | upper:2")
        self.assertEqual(error.message, "filter 'upper' takes no argument")


class ParseTest(unittest.TestCase):
    def assertSyntaxErrorAt(self, template: str, line: int, column: int) -> TemplateSyntaxError:
        with self.assertRaises(TemplateSyntaxError) as caught:
            parse(template)
        self.assertEqual((caught.exception.line, caught.exception.column), (line, column))
        return caught.exception

    def test_text_and_output(self):
        self.assertEqual(
            parse("Hi {{ name }}!"),
            [Text("Hi "), Output(_expr("name"), 1, 4), Text("!")],
        )
        self.assertEqual(parse(""), [])

    def test_if_with_and_without_else(self):
        self.assertEqual(
            parse("{% if a %}x{% else %}y{% endif %}"),
            [If(_expr("a"), [Text("x")], [Text("y")], 1, 1)],
        )
        self.assertEqual(parse("{%if a%}x{%endif%}"), [If(_expr("a"), [Text("x")], [], 1, 1)])

    def test_for_and_nested_blocks(self):
        tree = parse("{% for u in users %}{% if u.ok %}{{ u.name }}{% endif %}{% endfor %}")
        self.assertEqual(
            tree,
            [
                For(
                    "u",
                    _expr("users"),
                    [If(_expr("u", "ok"), [Output(_expr("u", "name"), 1, 34)], [], 1, 21)],
                    1,
                    1,
                )
            ],
        )

    def test_for_allows_any_whitespace_and_filters_in_the_tag(self):
        tree = parse("{%\tfor  x\nin  xs | upper %}{% endfor %}")
        self.assertEqual(tree, [For("x", _expr("xs", filters=(Filter("upper", None),)), [], 1, 1)])

    def test_comments_are_gone_from_the_tree(self):
        self.assertEqual(parse("a{# b #}c"), [Text("a"), Text("c")])

    def test_deep_nesting_does_not_hit_the_recursion_limit(self):
        depth = 5000
        tree = parse("{% if x %}" * depth + "{% endif %}" * depth)
        for _ in range(depth - 1):
            (tree,) = [node.body for node in tree]
        self.assertEqual(tree, [If(_expr("x"), [], [], 1, 10 * (depth - 1) + 1)])

    def test_lexer_errors_come_through(self):
        self.assertSyntaxErrorAt("{% if x %}\n{{ y", 2, 1)

    def test_bad_expression_in_output_if_and_for(self):
        self.assertSyntaxErrorAt("a\n b {{ x | nope }}", 2, 4)
        error = self.assertSyntaxErrorAt("{% if x | truncate:1 %}{% endif %}", 1, 1)
        self.assertEqual(error.message, "truncate width must be at least 3, got 1")
        self.assertSyntaxErrorAt("..{% for i in a..b %}{% endfor %}", 1, 3)

    def test_empty_and_unknown_tags(self):
        self.assertSyntaxErrorAt("ab{% %}", 1, 3)
        error = self.assertSyntaxErrorAt("\n\n  {% include x %}", 3, 3)
        self.assertEqual(error.message, "unknown tag 'include'")
        self.assertSyntaxErrorAt("{% elif x %}", 1, 1)
        self.assertSyntaxErrorAt("{% if(x) %}{% endif %}", 1, 1)

    def test_if_without_an_expression(self):
        self.assertSyntaxErrorAt("x{% if %}{% endif %}", 1, 2)

    def test_malformed_for(self):
        for template in ("{% for %}", "{% for x %}", "{% for x in %}", "{% for x of xs %}",
                         "{% for a.b in xs %}", "{% for a, b in xs %}", "{% for 1 in xs %}"):
            with self.subTest(template=template):
                self.assertSyntaxErrorAt(template + "{% endfor %}", 1, 1)

    def test_loop_is_reserved_as_a_loop_variable(self):
        error = self.assertSyntaxErrorAt(" {% for loop in xs %}{% endfor %}", 1, 2)
        self.assertIn("reserved", error.message)

    def test_closing_tags_without_their_opening_tag(self):
        self.assertSyntaxErrorAt("a\n{% else %}", 2, 1)
        self.assertSyntaxErrorAt("abc{% endif %}", 1, 4)
        error = self.assertSyntaxErrorAt("{% endfor %}", 1, 1)
        self.assertEqual(error.message, "'endfor' without an opening 'for'")
        # Closed already: the second endif has nothing to close.
        self.assertSyntaxErrorAt("{% if a %}{% endif %}{% endif %}", 1, 22)

    def test_a_closing_tag_must_match_the_innermost_open_block(self):
        error = self.assertSyntaxErrorAt("{% if a %}\n{% endfor %}", 2, 1)
        self.assertEqual(
            error.message, "'endfor' found while the 'if' at line 1, column 1 is still open"
        )
        self.assertSyntaxErrorAt("{% for x in xs %}{% if x %}{% endfor %}", 1, 28)
        # else belongs to if only.
        self.assertSyntaxErrorAt("{% for x in xs %}{% else %}{% endfor %}", 1, 18)

    def test_second_else(self):
        error = self.assertSyntaxErrorAt("{% if a %}1{% else %}2{% else %}3{% endif %}", 1, 23)
        self.assertEqual(error.message, "'if' already has an 'else'")

    def test_closing_tags_take_no_arguments(self):
        self.assertSyntaxErrorAt("{% if a %}{% endif a %}", 1, 11)
        self.assertSyntaxErrorAt("{% if a %}{% else if b %}{% endif %}", 1, 11)
        self.assertSyntaxErrorAt("{% for x in xs %}{% endfor x %}", 1, 18)

    def test_block_with_no_end_tag_is_reported_at_its_opening_tag(self):
        error = self.assertSyntaxErrorAt("a\n {% if x %}b", 2, 2)
        self.assertEqual(error.message, "'if' is never closed with 'endif'")
        self.assertSyntaxErrorAt("{% for x in xs %}{% if x %}{% else %}", 1, 18)
        self.assertSyntaxErrorAt("{% for x in xs %}{% if x %}{% endif %}", 1, 1)


if __name__ == "__main__":
    unittest.main()
