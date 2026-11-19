"""Tests for textkit.templates (plan task T3.12)."""

import types
import unittest

from textkit.templates import render


class RenderTest(unittest.TestCase):
    def test_plan_cases(self):
        self.assertEqual(render("{{x}}", {}), "{x}")
        self.assertEqual(render("{{{x}}}", {"x": 1}), "{1}")

    def test_replaces_placeholders(self):
        self.assertEqual(render("Hi {name}, {name}!", {"name": "Ana"}), "Hi Ana, Ana!")
        self.assertEqual(render("{_a1}{B}", {"_a1": "x", "B": "y"}), "xy")

    def test_plain_text_and_empty(self):
        self.assertEqual(render("", {}), "")
        self.assertEqual(render("no braces", {}), "no braces")
        self.assertEqual(render("a", {}), "a")

    def test_values_go_through_str_only(self):
        self.assertEqual(render("{x}", {"x": None}), "None")
        self.assertEqual(render("{x}", {"x": 3.5}), "3.5")

        class Odd:
            def __str__(self):
                return "str"

            def __format__(self, spec):
                return "format"

        self.assertEqual(render("{x}", {"x": Odd()}), "str")

    def test_value_text_is_not_rendered_again(self):
        self.assertEqual(render("{x}", {"x": "{y}"}), "{y}")

    def test_accepts_any_mapping(self):
        self.assertEqual(render("{x}", types.MappingProxyType({"x": 1})), "1")

    def test_invalid_syntax_raises_value_error(self):
        for template in ["{}", "{0}", "{ x }", "{x:>5}", "{x!r}", "a } b", "a { b",
                         "{a.b}", "{a[0]}", "{", "}", "{x", "x}", "{{x}", "{1a}", "{a{b}",
                         "{x\n}", "{é}"]:
            with self.subTest(template=template):
                with self.assertRaises(ValueError):
                    render(template, {"x": 1, "a": 1})

    def test_validates_before_lookup(self):
        with self.assertRaises(ValueError):
            render("{a.b}", {})
        with self.assertRaises(ValueError):
            render("{y} {", {})

    def test_missing_name_raises_key_error(self):
        with self.assertRaises(KeyError) as ctx:
            render("{y}", {"x": 1})
        self.assertEqual(ctx.exception.args, ("y",))

    def test_non_str_template_raises_type_error(self):
        with self.assertRaises(TypeError):
            render(None, {})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
