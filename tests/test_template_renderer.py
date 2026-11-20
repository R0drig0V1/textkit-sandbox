"""Tests for textkit/template/renderer.py and the public ``textkit.template.render`` (T3.4).

``RenderTest.test_adr_cases`` runs every row of the case table of the ADR on missing names
(found by its slug, ``*-template-missing-names.md``, never by number), and
``test_cases_match_adr_table`` parses that table with ``ast.literal_eval`` and checks that it
equals ``RENDER_CASES``, so the ADR and the tests cannot drift apart.
"""

import ast
import pathlib
import re
import unittest

import textkit.template
from textkit.template import TemplateError, TemplateSyntaxError
from textkit.template.renderer import render

ROOT = pathlib.Path(__file__).resolve().parents[1]

_IF = "{% if x %}y{% else %}n{% endif %}"
_IF_USER = "{% if user.name %}y{% else %}n{% endif %}"
_FOR = "{% for i in xs %}{{ i }}{% endfor %}"

# (template, context, outcome): the output, or (error class name, line, column). The same
# rows, in the same order, as the "## Cases" table of the ADR.
RENDER_CASES = [
    ("Hello {{ name }}!", {"name": "Ada"}, "Hello Ada!"),
    ("Hello {{ name }}!", {}, ("TemplateError", 1, 7)),
    ("{{ user.name }}", {"user": {}}, ("TemplateError", 1, 1)),
    ("{{ user.name }}", {"user": "Ada"}, ("TemplateError", 1, 1)),
    ("{{ user.name }}", {"user": None}, ("TemplateError", 1, 1)),
    ("[{{ x }}]", {"x": None}, "[]"),
    ("[{{ x | upper }}]", {"x": None}, "[]"),
    ("[{{ x }}]", {"x": ""}, "[]"),
    ("{{ t }} {{ f }}", {"t": True, "f": False}, "True False"),
    ("{{ f | lower }}", {"f": False}, "false"),
    ("{{ n }} {{ z }} {{ r }}", {"n": 42, "z": 0, "r": 1.5}, "42 0 1.5"),
    (_IF, {}, "n"),
    (_IF, {"x": None}, "n"),
    (_IF, {"x": False}, "n"),
    (_IF, {"x": True}, "y"),
    (_IF, {"x": 0}, "n"),
    (_IF, {"x": 0.0}, "n"),
    (_IF, {"x": -1}, "y"),
    (_IF, {"x": ""}, "n"),
    (_IF, {"x": "0"}, "y"),
    (_IF, {"x": []}, "n"),
    (_IF, {"x": {}}, "n"),
    (_IF_USER, {}, "n"),
    (_IF_USER, {"user": {}}, "n"),
    (_IF_USER, {"user": "Ada"}, ("TemplateError", 1, 1)),
    (_IF_USER, {"user": None}, ("TemplateError", 1, 1)),
    ("{% if x | lower %}y{% else %}n{% endif %}", {"x": False}, "y"),
    ("{% if x | lower %}y{% else %}n{% endif %}", {}, "n"),
    ("{% if x %}{{ y }}{% endif %}", {}, ""),
    ("{% if x %}{{ y }}{% endif %}", {"x": 1}, ("TemplateError", 1, 11)),
    ("{% if x %}{{ y | nope }}{% endif %}", {}, ("TemplateSyntaxError", 1, 11)),
    (_FOR, {}, ("TemplateError", 1, 1)),
    (_FOR, {"xs": None}, ("TemplateError", 1, 1)),
    (_FOR, {"xs": "ab"}, ("TemplateError", 1, 1)),
    (_FOR, {"xs": []}, ""),
    (_FOR, {"xs": [1, None, True, 2.5]}, "1True2.5"),
    (
        "{% for i in xs %}{{ loop.index }}{% endfor %}{{ loop }}",
        {"xs": ["a", "b"], "loop": "L"},
        "12L",
    ),
    ("{{ loop.index }}", {}, ("TemplateError", 1, 1)),
    ("a\n{{ b }}", {}, ("TemplateError", 2, 1)),
    ("a\r\n  {{ b }}", {}, ("TemplateError", 2, 3)),
    ("a\r{{ b }}", {}, ("TemplateError", 1, 3)),
    ("{{ x }}", {"x": "{{ y }}"}, "{{ y }}"),
]

# One table row: three cells, each a Python literal in backticks.
_ROW = re.compile(r"^\| `(.*?)` \| `(.*?)` \| `(.*?)` \|$", re.M)


def _adr_cases() -> list:
    """Parse the case table of the missing-names ADR, found by slug, into (t, c, outcome)."""
    (adr,) = (ROOT / "docs" / "decisions").glob("*-template-missing-names.md")
    table = adr.read_text(encoding="utf-8").split("\n## Cases\n", 1)[1]
    return [
        tuple(ast.literal_eval(cell) for cell in row) for row in _ROW.findall(table)
    ]


def _outcome(template: str, context: dict):
    """What ``render`` gives: the text, or (error class name, line, column)."""
    try:
        return render(template, context)
    except TemplateError as error:
        return (type(error).__name__, error.line, error.column)


class RenderTest(unittest.TestCase):
    def assertErrorAt(self, cls: type, template: str, context: dict, line: int, column: int):
        with self.assertRaises(cls) as caught:
            render(template, context)
        self.assertIs(type(caught.exception), cls)
        self.assertEqual((caught.exception.line, caught.exception.column), (line, column))
        return caught.exception

    def test_adr_cases(self):
        for template, context, expected in RENDER_CASES:
            with self.subTest(template=template, context=context):
                self.assertEqual(_outcome(template, context), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(RENDER_CASES, _adr_cases())

    def test_text_is_copied_exactly_and_never_escaped(self):
        for text in ("", "plain", "a\r\nb\rc\n", "<b>&amp;\"'</b>", "{ x } }} %} #}"):
            with self.subTest(text=text):
                self.assertEqual(render(text, {}), text)
        self.assertEqual(render("{{ h }}", {"h": "<i>&</i>"}), "<i>&</i>")
        self.assertEqual(
            render("{% for x in xs %}{{ x }}\r\n{% endfor %}", {"xs": [1, 2]}), "1\r\n2\r\n"
        )

    def test_spaces_inside_delimiters_are_optional(self):
        context = {"x": "a", "xs": [1]}
        self.assertEqual(
            render("{{x}}{%if x%}y{%else%}n{%endif%}{%for i in xs%}{{i}}{%endfor%}", context),
            render("{{ x }}{% if x %}y{% else %}n{% endif %}{% for i in xs %}{{ i }}{% endfor %}",
                   context),
        )

    def test_comments_print_nothing(self):
        self.assertEqual(render("a{# {{ missing }} #}b", {}), "ab")

    def test_each_filter(self):
        cases = [
            ("slug", "Hello, World!", "hello-world"),
            ("snake", "userId", "user_id"),
            ("camel", "user_id", "userId"),
            ("kebab", "userId", "user-id"),
            ("squeeze", "  a \n b ", "a b"),
            ("strip_accents", "Ñandú", "Nandu"),
            ("truncate:8", "Hello, World!", "Hello..."),
            ("truncate:20", "short", "short"),
            ("upper", "Ada", "ADA"),
            ("lower", "Ada", "ada"),
        ]
        for flt, value, expected in cases:
            with self.subTest(filter=flt):
                self.assertEqual(render("{{ v | " + flt + " }}", {"v": value}), expected)

    def test_filters_apply_left_to_right_to_the_printed_text(self):
        context = {"t": "Hello, World Again"}
        self.assertEqual(render("{{ t | slug | truncate:8 }}", context), "hello...")
        self.assertEqual(render("{{ t | truncate:8 | slug }}", context), "hello")
        self.assertEqual(render("{{ n | truncate:4 }}", {"n": 123456}), "1...")

    def test_dotted_names_follow_dict_keys(self):
        context = {"user": {"address": {"city": "Lima"}, "items": [1]}}
        self.assertEqual(render("{{ user.address.city }}", context), "Lima")
        self.assertEqual(render("{{ user.items }}", context), "[1]")
        error = self.assertErrorAt(TemplateError, "\n {{ user.items.first }}", context, 2, 2)
        self.assertIn("'user.items' is a list, not a dict", error.message)

    def test_loop_index_and_nested_loops(self):
        template = (
            "{% for row in rows %}{{ loop.index }}:"
            "{% for c in row %}{{ loop.index }}{{ c }}{{ row | lower }}{% endfor %};"
            "{{ loop.index }}{% endfor %}"
        )
        self.assertEqual(
            render(template, {"rows": [["a"], ["b", "c"]]}),
            "1:1a['a'];12:1b['b', 'c']2c['b', 'c'];2",
        )

    def test_loop_variable_hides_a_context_key_only_inside_the_loop(self):
        template = "{{ x }}{% for x in xs %}{{ x }}{% endfor %}{{ x }}"
        self.assertEqual(render(template, {"x": "o", "xs": [1, 2]}), "o12o")

    def test_for_needs_a_list(self):
        for value in ((1, 2), {"a": 1}, "ab", 3, True):
            with self.subTest(value=value):
                self.assertErrorAt(TemplateError, "x\n{% for i in v %}{% endfor %}",
                                   {"v": value}, 2, 1)
        error = self.assertErrorAt(TemplateError, "{% for i in v | upper %}{% endfor %}",
                                   {"v": ["a"]}, 1, 1)
        self.assertIn("needs a list", error.message)

    def test_render_time_errors_in_nested_blocks_point_at_their_tag(self):
        template = (
            "{% for u in users %}\n  {% if u.ok %}\n    {{ u.name }}\n  {% endif %}\n"
            "{% endfor %}"
        )
        error = self.assertErrorAt(TemplateError, template, {"users": [{"ok": True}]}, 3, 5)
        self.assertEqual(error.message, "'u' has no key 'name'")
        self.assertErrorAt(TemplateError, template, {"users": ["x"]}, 2, 3)

    def test_syntax_errors_are_raised_before_any_output(self):
        # The bad tag sits in a branch the context never reaches.
        self.assertErrorAt(TemplateSyntaxError, "{% if no %}{% if %}{% endif %}{% endif %}",
                           {}, 1, 12)

    def test_rejects_arguments_of_the_wrong_type(self):
        with self.assertRaises(TypeError):
            render(b"{{ x }}", {"x": 1})
        with self.assertRaises(TypeError):
            render("{{ x }}", [("x", 1)])

    def test_error_classes(self):
        self.assertTrue(issubclass(TemplateSyntaxError, TemplateError))
        # Phase 3 rule "Errors": ValueError until the error hierarchy (T3.2) is merged.
        self.assertTrue(issubclass(TemplateError, ValueError))
        error = TemplateError("boom", 3, 14)
        self.assertEqual((error.message, error.line, error.column), ("boom", 3, 14))
        self.assertEqual(str(error), "3:14: boom")

    def test_package_exports_render_only(self):
        self.assertEqual(textkit.template.__all__, ["render"])
        self.assertIs(textkit.template.render, render)
        self.assertIs(textkit.template.TemplateError, TemplateError)


if __name__ == "__main__":
    unittest.main()
