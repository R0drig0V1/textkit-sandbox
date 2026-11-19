"""Tests for textkit.templates, one TestCase class per public function.

RenderTest covers every example and test listed in plan task T3.12
(docs/phases/phase-3-converters.md), the phase-3 rule that the function is called with
``"a"`` and raises nothing but ``ValueError``, ``KeyError`` or ``TypeError``, and the points
of the grammar the task states in prose: validation before lookup, ``str()`` only, no
re-parsing of inserted values.
"""

import collections
import unittest

from textkit.templates import render


class RenderTest(unittest.TestCase):
    """``render(template, values)``: the T3.12 grammar."""

    def test_task_examples(self) -> None:
        cases = [
            ("{{x}}", {}, "{x}"),
            ("{{{x}}}", {"x": 1}, "{1}"),
        ]
        for template, values, expected in cases:
            with self.subTest(template=template):
                self.assertEqual(render(template, values), expected)

    def test_placeholders(self) -> None:
        cases = [
            ("", {}, ""),
            ("a", {}, "a"),
            ("{x}", {"x": "y"}, "y"),
            ("Hello, {name}!", {"name": "Ada"}, "Hello, Ada!"),
            ("{a}{b}{a}", {"a": 1, "b": 2}, "121"),
            ("{_}", {"_": "u"}, "u"),
            ("{A_1}", {"A_1": "ok"}, "ok"),
            ("{x}", {"x": None}, "None"),
            ("{x}", {"x": 1.5}, "1.5"),
            ("{x}", {"x": [1, 2]}, "[1, 2]"),
            ("}}{{", {}, "}{"),
            ("{{}}", {}, "{}"),
            ("ü {x} ü", {"x": "ñ"}, "ü ñ ü"),
        ]
        for template, values, expected in cases:
            with self.subTest(template=template):
                self.assertEqual(render(template, values), expected)

    def test_invalid_templates_raise_value_error(self) -> None:
        # The first nine are the task's list; the rest are other brace content it names
        # (digits, spaces, "[", "!", ":") or a non-ASCII name.
        templates = [
            "{}", "{0}", "{ x }", "{x:>5}", "{x!r}", "a } b", "a { b", "{a.b}", "{a[0]}",
            "{", "}", "{x", "x}", "{1x}", "{x }", "{x\n}", "{{x}", "{x}}", "{a{b}", "{é}",
            "{{{x}}",
        ]
        for template in templates:
            with self.subTest(template=template):
                with self.assertRaises(ValueError):
                    render(template, {"x": 1, "a": {"b": 2}})

    def test_validation_before_lookup(self) -> None:
        # The invalid placeholder comes after a missing name, so a left-to-right lookup
        # would raise KeyError first; the task requires ValueError.
        for template in ("{a.b}", "{missing} {a.b}", "{missing} }"):
            with self.subTest(template=template):
                with self.assertRaises(ValueError):
                    render(template, {})

    def test_missing_name_raises_key_error(self) -> None:
        with self.assertRaises(KeyError) as ctx:
            render("{y}", {"x": 1})
        self.assertEqual(ctx.exception.args, ("y",))

    def test_first_missing_name_from_the_left(self) -> None:
        with self.assertRaises(KeyError) as ctx:
            render("{b} {c}", {"a": 1})
        self.assertEqual(ctx.exception.args, ("b",))

    def test_values_go_through_str_only(self) -> None:
        class Loud:
            def __str__(self) -> str:
                return "str"

            def __format__(self, spec: str) -> str:
                return "format"

            def __repr__(self) -> str:
                return "repr"

        self.assertEqual(render("{x}", {"x": Loud()}), "str")

    def test_inserted_values_are_not_parsed_again(self) -> None:
        self.assertEqual(render("{x}", {"x": "{y} }{"}), "{y} }{")

    def test_any_mapping(self) -> None:
        self.assertEqual(render("{x}", collections.OrderedDict(x=1)), "1")
        # A Mapping's own missing-key behaviour is used: a defaultdict fills the gap.
        self.assertEqual(render("{x}", collections.defaultdict(lambda: "d")), "d")

    def test_called_with_a(self) -> None:
        # Phase-3 rule: called with "a", the function raises only ValueError, KeyError or
        # TypeError (here: no exception for a template without braces, TypeError otherwise).
        self.assertEqual(render("a", {}), "a")
        for args in (("a",), ("a", "a"), ("{a}", "a")):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    render(*args)  # type: ignore[arg-type]

    def test_type_errors(self) -> None:
        for template, values in ((1, {}), (None, {}), (b"{x}", {"x": 1}), ("{x}", [("x", 1)])):
            with self.subTest(template=template, values=values):
                with self.assertRaises(TypeError):
                    render(template, values)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
