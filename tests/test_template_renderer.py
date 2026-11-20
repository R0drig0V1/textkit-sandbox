"""Tests for ``textkit.template.renderer`` and the package entry point (plan task T3.4).

``CASES`` is the case table of the missing-names ADR (found by its slug, never by number:
``docs/decisions/*-template-missing-names.md``), row by row; ``AdrCasesTest`` checks that
the two are equal and that every row renders as stated, so they cannot drift apart.
"""

import ast
import pathlib
import sys
import unittest

import textkit.template
from textkit.template import TemplateError, TemplateSyntaxError, renderer

ROOT = pathlib.Path(__file__).resolve().parents[1]

_IF = "{% if X %}yes{% else %}no{% endif %}"

# (template, context, outcome): outcome is the output, or (error class name, line, column).
CASES = [
    ("{{ name }}", {"name": "Ada"}, "Ada"),
    ("Hi {{ name }}!", {}, ("TemplateError", 1, 4)),
    ("{{ name | upper }}", {}, ("TemplateError", 1, 1)),
    ("{{ user.name }}", {}, ("TemplateError", 1, 1)),
    ("{{ user.name }}", {"user": {}}, ("TemplateError", 1, 1)),
    ("{{ user.name }}", {"user": "Ada"}, ("TemplateError", 1, 1)),
    ("{{ user.name }}", {"user": None}, ("TemplateError", 1, 1)),
    ("a\n{{ b }}", {}, ("TemplateError", 2, 1)),
    (_IF.replace("X", "name"), {}, "no"),
    (_IF.replace("X", "user.admin"), {}, "no"),
    (_IF.replace("X", "user.admin"), {"user": {}}, "no"),
    (_IF.replace("X", "user.admin"), {"user": None}, ("TemplateError", 1, 1)),
    (_IF.replace("X", "name | upper"), {}, "no"),
    ("{% for x in items %}{{ x }}{% endfor %}", {}, ("TemplateError", 1, 1)),
    ("{% for x in items %}{{ x.y }}{% endfor %}", {"items": [{}]}, ("TemplateError", 1, 21)),
    (
        "{% for x in items %}{{ loop.size }}{% endfor %}",
        {"items": [1]},
        ("TemplateError", 1, 21),
    ),
    ("[{{ x }}]", {"x": None}, "[]"),
    ("[{{ x | upper }}]", {"x": None}, "[]"),
    (_IF.replace("X", "x"), {"x": None}, "no"),
    ("{% for x in items %}{{ x }}{% endfor %}", {"items": None}, ("TemplateError", 1, 1)),
    ("{% for x in items %}[{{ x }}]{% endfor %}", {"items": [None, "a"]}, "[][a]"),
    ("{{ x }}", {"x": True}, "True"),
    ("{{ x }}", {"x": False}, "False"),
    ("{{ x | lower }}", {"x": True}, "true"),
    (_IF.replace("X", "x"), {"x": True}, "yes"),
    (_IF.replace("X", "x"), {"x": False}, "no"),
    (_IF.replace("X", "x | lower"), {"x": False}, "yes"),
    ("{{ n }}", {"n": 0}, "0"),
    ("{{ n }}", {"n": -12}, "-12"),
    ("{{ n }}", {"n": 2.5}, "2.5"),
    (_IF.replace("X", "n"), {"n": 0}, "no"),
    (_IF.replace("X", "n"), {"n": 0.0}, "no"),
    (_IF.replace("X", "n | lower"), {"n": 0}, "yes"),
    (_IF.replace("X", "s"), {"s": ""}, "no"),
    (_IF.replace("X", "s"), {"s": "0"}, "yes"),
    (_IF.replace("X", "xs"), {"xs": []}, "no"),
]


def _adr_cases() -> list:
    """Parse the ``## Cases`` table of the missing-names ADR into (template, context, outcome)."""
    (adr,) = (ROOT / "docs" / "decisions").glob("*-template-missing-names.md")
    table = adr.read_text(encoding="utf-8").split("\n## Cases\n", 1)[1]
    rows = []
    for line in table.splitlines():
        if not line.startswith("| `"):
            continue  # the header, its separator line and blank lines
        # Cells never contain " | ": a "|" inside one is written \x7c (phase 3 rule "ADRs").
        cells = line.strip().strip("|").split(" | ")
        rows.append(tuple(ast.literal_eval(cell.strip().strip("`")) for cell in cells))
    return rows


def _outcome(template: str, context: dict) -> object:
    """Render, or return (error class name, line, column) for a ``TemplateError``."""
    try:
        return renderer.render(template, context)
    except TemplateError as error:
        return (type(error).__name__, error.line, error.column)


class AdrCasesTest(unittest.TestCase):
    def test_cases_match_adr_table(self):
        self.assertEqual(CASES, _adr_cases())

    def test_adr_cases(self):
        for template, context, expected in CASES:
            with self.subTest(template=template, context=context):
                self.assertEqual(_outcome(template, context), expected)


class RenderTest(unittest.TestCase):
    def test_text_is_copied_as_is(self):
        text = "a < b & \"c\"\r\n\ttabs { braces } %\r\n"
        self.assertEqual(renderer.render(text, {}), text)

    def test_empty_template(self):
        self.assertEqual(renderer.render("", {"x": 1}), "")

    def test_values_are_not_escaped(self):
        self.assertEqual(renderer.render("{{ x }}", {"x": "<b>&</b>"}), "<b>&</b>")

    def test_crlf_around_tags_stays_crlf(self):
        self.assertEqual(
            renderer.render("{% if a %}\r\n{{ a }}\r\n{% endif %}\r\n", {"a": "x"}),
            "\r\nx\r\n\r\n",
        )

    def test_comments_print_nothing(self):
        self.assertEqual(renderer.render("a{# {{ missing }} #}b", {}), "ab")

    def test_dotted_names_follow_dict_keys(self):
        context = {"a": {"b": {"c": "deep"}}}
        self.assertEqual(renderer.render("{{ a.b.c }}", context), "deep")

    def test_dotted_names_do_not_follow_attributes(self):
        # "a.real" is not a dict key of an int, even though ints have a .real attribute.
        with self.assertRaises(TemplateError):
            renderer.render("{{ a.real }}", {"a": 3})

    def test_values_print_with_str(self):
        self.assertEqual(renderer.render("{{ x }}", {"x": [1, "a"]}), "[1, 'a']")
        self.assertEqual(renderer.render("{{ x }}", {"x": {"k": 1}}), "{'k': 1}")

    def test_every_filter(self):
        context = {"t": "Héllo, Wörld  HTTPServer user_id"}
        expected = {
            "slug": "hllo-wrld-httpserver-user-id",
            "snake": "héllo_wörld_http_server_user_id",
            "camel": "h\u00e9llo, w\u00f6rld  httpserver userId",
            "kebab": "héllo-wörld-http-server-user-id",
            "squeeze": "Héllo, Wörld HTTPServer user_id",
            "strip_accents": "Hello, World  HTTPServer user_id",
            "truncate:10": "Héllo, ...",
            "upper": "HÉLLO, WÖRLD  HTTPSERVER USER_ID",
            "lower": "héllo, wörld  httpserver user_id",
        }
        for spec, output in expected.items():
            with self.subTest(filter=spec):
                self.assertEqual(renderer.render("{{ t | %s }}" % spec, context), output)

    def test_filters_chain_left_to_right(self):
        context = {"title": "  Hello,   World of Templates "}
        self.assertEqual(
            renderer.render("{{ title | slug | truncate:12 }}", context), "hello-wor..."
        )
        self.assertEqual(renderer.render("{{ title | squeeze | upper }}", context),
                         "HELLO, WORLD OF TEMPLATES")

    def test_filters_apply_to_str_of_the_value(self):
        self.assertEqual(renderer.render("{{ n | truncate:4 }}", {"n": 123456}), "1...")

    def test_if_uses_python_truth(self):
        template = "{% if x %}T{% else %}F{% endif %}"
        for value, expected in [([0], "T"), ({}, "F"), ({"a": 1}, "T"), (" ", "T")]:
            with self.subTest(value=value):
                self.assertEqual(renderer.render(template, {"x": value}), expected)

    def test_for_with_loop_index(self):
        self.assertEqual(
            renderer.render(
                "{% for c in colors %}{{ loop.index }}={{ c }};{% endfor %}",
                {"colors": ["red", "green"]},
            ),
            "1=red;2=green;",
        )

    def test_for_over_empty_list_prints_nothing(self):
        self.assertEqual(renderer.render("[{% for x in xs %}x{% endfor %}]", {"xs": []}), "[]")

    def test_loop_is_the_innermost_loop(self):
        template = (
            "{% for row in rows %}{% for cell in row %}"
            "{{ loop.index }}{% endfor %}/{{ loop.index }} {% endfor %}"
        )
        self.assertEqual(
            renderer.render(template, {"rows": [["a", "b", "c"], ["d"]]}), "123/1 1/2 "
        )

    def test_loop_hides_a_context_key_named_loop(self):
        context = {"loop": {"index": "ctx"}, "xs": ["a"]}
        self.assertEqual(
            renderer.render("{{ loop.index }}{% for x in xs %}{{ loop.index }}{% endfor %}"
                            "{{ loop.index }}", context),
            "ctx1ctx",
        )

    def test_loop_variable_shadows_and_is_restored(self):
        context = {"x": "outer", "xs": ["inner"]}
        self.assertEqual(
            renderer.render("{{ x }}{% for x in xs %}{{ x }}{% endfor %}{{ x }}", context),
            "outerinnerouter",
        )

    def test_loop_variable_is_gone_after_the_loop(self):
        with self.assertRaises(TemplateError) as caught:
            renderer.render("{% for y in xs %}{% endfor %}\n{{ y }}", {"xs": [1]})
        self.assertEqual((caught.exception.line, caught.exception.column), (2, 1))

    def test_for_over_a_value_that_is_not_a_list(self):
        for value in ("abc", ("a",), {"a": 1}, 3):
            with self.subTest(value=value):
                with self.assertRaises(TemplateError) as caught:
                    renderer.render("x\n {% for i in v %}{% endfor %}", {"v": value})
                self.assertNotIsInstance(caught.exception, TemplateSyntaxError)
                self.assertEqual((caught.exception.line, caught.exception.column), (2, 2))
                self.assertIn("needs a list", caught.exception.message)

    def test_for_over_a_filtered_value_is_an_error(self):
        with self.assertRaises(TemplateError) as caught:
            renderer.render("{% for i in v | upper %}{% endfor %}", {"v": ["a"]})
        self.assertIn("filters turn", caught.exception.message)

    def test_dotted_name_through_a_non_dict_reports_the_prefix(self):
        with self.assertRaises(TemplateError) as caught:
            renderer.render("{{ a.b.c }}", {"a": {"b": [1]}})
        self.assertIn("'a.b'", caught.exception.message)
        self.assertIn("list", caught.exception.message)

    def test_missing_name_message(self):
        with self.assertRaises(TemplateError) as caught:
            renderer.render("ab\r\ncd {{ user.nmae }}", {"user": {"name": "x"}})
        error = caught.exception
        self.assertEqual((error.line, error.column), (2, 4))
        self.assertEqual(str(error), "2:4: 'user.nmae' is not defined")

    def test_syntax_errors_come_before_any_rendering(self):
        # The missing name comes first in the text, but the template does not parse.
        with self.assertRaises(TemplateSyntaxError):
            renderer.render("{{ missing }}{% endif %}", {})

    def test_huge_truncate_width_is_a_syntax_error(self):
        with self.assertRaises(TemplateSyntaxError) as caught:
            renderer.render("x\n {{ t | truncate:" + "9" * 5000 + " }}", {"t": "abc"})
        self.assertEqual((caught.exception.line, caught.exception.column), (2, 2))

    def test_large_truncate_width_keeps_the_text(self):
        template = "{{ t | truncate:" + "9" * 18 + " }}"
        self.assertEqual(renderer.render(template, {"t": "abc"}), "abc")

    def test_value_whose_str_raises_value_error(self):
        class Unprintable:
            def __str__(self) -> str:
                raise ValueError("no text for this value")

        for template in ("ab {{ v }}", "ab {% if v | upper %}{% endif %}"):
            with self.subTest(template=template):
                with self.assertRaises(TemplateError) as caught:
                    renderer.render(template, {"v": Unprintable()})
                error = caught.exception
                self.assertEqual((error.line, error.column), (1, 4))
                self.assertEqual(error.message, "cannot print 'v': no text for this value")

    def test_int_too_long_to_print(self):
        # str() of an int of more than 4300 digits raises ValueError where the interpreter
        # limits integer string conversion (3.11+, 3.9.14+); elsewhere it prints.
        context = {"x": 10**5000, "xs": [10**5000]}
        for template in ("{{ x }}", "{{ xs }}"):
            with self.subTest(template=template):
                if hasattr(sys, "get_int_max_str_digits"):
                    with self.assertRaises(TemplateError) as caught:
                        renderer.render(template, context)
                    self.assertEqual((caught.exception.line, caught.exception.column), (1, 1))
                    self.assertIn("cannot print", caught.exception.message)
                else:
                    self.assertIn("1" + "0" * 5000, renderer.render(template, context))

    def test_wrong_argument_types(self):
        with self.assertRaises(TypeError):
            renderer.render(b"{{ x }}", {"x": 1})
        with self.assertRaises(TypeError):
            renderer.render("{{ x }}", [("x", 1)])

    def test_context_is_not_modified(self):
        context = {"xs": [1, 2], "x": "keep"}
        renderer.render("{% for x in xs %}{{ x }}{% endfor %}", context)
        self.assertEqual(context, {"xs": [1, 2], "x": "keep"})


class PackageTest(unittest.TestCase):
    def test_all_lists_functions_only(self):
        self.assertEqual(textkit.template.__all__, ["render"])
        self.assertIs(textkit.template.render, renderer.render)

    def test_errors_are_importable_from_the_package(self):
        from textkit.template.exceptions import TemplateError as Defined

        self.assertIs(textkit.template.TemplateError, Defined)
        self.assertTrue(issubclass(textkit.template.TemplateSyntaxError, Defined))


if __name__ == "__main__":
    unittest.main()
