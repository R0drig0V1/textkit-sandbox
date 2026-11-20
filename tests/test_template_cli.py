"""Tests for ``python3 -m textkit render`` (``textkit/cli/render.py``, plan task T3.4).

Every test runs the real command line in a subprocess through ``_run`` or ``_run_bytes`` from
``tests/test_cli.py`` (repository root as cwd, ``PYTHONIOENCODING=utf-8``), with its input
files written to a fresh ``tempfile`` directory and passed as absolute paths, so parallel
runs of the checks never share a file (phase 3 rule "The command line"). Every exit code
(0, 1, 2) is covered.
"""

import json
import pathlib
import tempfile
import unittest
from typing import Union

from tests.test_cli import _run, _run_bytes
from textkit.cli import render as render_command
from textkit.cli.registry import PROG, commands

ERROR = f"{PROG} render: error: "


class RenderCommandTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def _file(self, name: str, data: Union[str, bytes]) -> str:
        """Write ``data`` (UTF-8 for ``str``, no newline translation) and return its path."""
        path = self.tmp / name
        path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return str(path)

    def _context(self, value: object) -> str:
        return self._file("context.json", json.dumps(value))

    def test_registered_under_its_module_name(self):
        self.assertIn(render_command.COMMAND, commands())
        self.assertEqual(render_command.COMMAND.name, "render")

    def test_renders_to_stdout_unchanged(self):
        template = self._file("t.txt", "Hi {{ user.name | upper }}, {{ n }} new")
        result = _run("render", template, self._context({"user": {"name": "Añá"}, "n": 3}))
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        # No newline is added to the result.
        self.assertEqual(result.stdout, "Hi AÑÁ, 3 new")

    def test_crlf_and_lone_cr_are_kept(self):
        template = self._file(
            "t.txt", "{% for x in xs %}{{ loop.index }}:{{ x }}\r\n{% endfor %}end\r"
        )
        result = _run_bytes("render", template, self._context({"xs": ["a", "b"]}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1:a\r\n2:b\r\nend\r".encode("utf-8"))

    def test_empty_result_writes_nothing(self):
        template = self._file("t.txt", "{% if missing %}x{% endif %}{# only a comment #}")
        result = _run_bytes("render", template, self._context({}))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_template_error_exits_1_with_line_and_column(self):
        template = self._file("t.txt", "Dear\r\n  {{ nmae }}")
        result = _run("render", template, self._context({"name": "Ada"}))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "2:3: 'nmae' is not defined\n")

    def test_syntax_error_exits_1_with_line_and_column(self):
        template = self._file("t.txt", "a\n\n{% if x %}never closed")
        result = _run("render", template, self._context({"x": True}))
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertEqual(result.stderr, "3:1: 'if' has no 'endif'\n")

    def test_unreadable_files_exit_2(self):
        good_template = self._file("t.txt", "{{ x }}")
        good_context = self._context({"x": 1})
        missing = str(self.tmp / "missing.txt")
        directory = str(self.tmp)
        for args, path in [
            ((missing, good_context), missing),
            ((good_template, missing), missing),
            ((directory, good_context), directory),
        ]:
            with self.subTest(args=args):
                result = _run("render", *args)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertTrue(result.stderr.startswith(f"{ERROR}{path}: "), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_exits_2(self):
        template = self._file("t.txt", b"ok \xff{{ x }}")
        result = _run("render", template, self._context({"x": 1}))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr, f"{ERROR}{template}: not valid UTF-8 (byte 0xff at offset 3)\n"
        )

    def test_context_that_is_not_json_exits_2(self):
        template = self._file("t.txt", "{{ x }}")
        context = self._file("context.json", "{x: 1}")
        result = _run("render", template, context)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{ERROR}{context}: not valid JSON: "))
        self.assertNotIn("Traceback", result.stderr)

    def test_context_that_is_not_an_object_exits_2(self):
        template = self._file("t.txt", "{{ x }}")
        for value, kind in [([1, 2], "list"), ("x", "str"), (None, "NoneType")]:
            with self.subTest(value=value):
                context = self._context(value)
                result = _run("render", template, context)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stderr, f"{ERROR}{context}: not a JSON object (got a JSON {kind})\n"
                )

    def test_wrong_argument_count_exits_2(self):
        result = _run("render", self._file("t.txt", "x"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("<json-file>", result.stderr)

    def test_help_lists_render_under_tools(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        tools = result.stdout.split("\ntools:\n", 1)[1]
        self.assertRegex(tools, r"(?m)^  render\s+Render a template file")


if __name__ == "__main__":
    unittest.main()
