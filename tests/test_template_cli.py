"""Tests for textkit/cli/render.py, the ``python3 -m textkit render`` tool (plan task T3.4).

Every test runs the real command line in a subprocess through ``_run`` and ``_run_bytes`` of
``tests/test_cli.py`` (cwd the repository root, ``PYTHONIOENCODING=utf-8``), with its input
files written to a fresh ``tempfile`` directory and passed as absolute paths, so parallel
runs never share a file. ``_run`` decodes in text mode, which turns ``"\\r"`` into
``"\\n"``; outputs that contain ``"\\r"`` are checked with ``_run_bytes``. One test calls the
tool's ``run`` in process, to give it a stdout whose encoding cannot hold the result.
"""

import argparse
import contextlib
import io
import json
import pathlib
import tempfile
import unittest

import textkit.cli.render as render_cli
from tests.test_cli import _run, _run_bytes

PREFIX = "python3 -m textkit render: error: "


class RenderCommandTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = pathlib.Path(tmp.name)

    def _file(self, name: str, content) -> str:
        """Write ``content`` (text as UTF-8 with no newline translation, or bytes) to ``name``."""
        path = self.dir / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_bytes(content.encode("utf-8"))
        return str(path)

    def _json(self, value) -> str:
        return self._file("context.json", json.dumps(value))

    def test_renders_to_stdout_without_adding_a_newline(self):
        template = self._file("t.txt", "Hi {{ user.name | upper }}!{% if n %} n={{ n }}{% endif %}")
        result = _run("render", template, self._json({"user": {"name": "Ada"}, "n": None}))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "Hi ADA!", ""))

    def test_json_null_and_unicode(self):
        template = self._file("t.txt", "[{{ a }}] {{ b | strip_accents }}\n")
        result = _run("render", template, self._json({"a": None, "b": "Ñandú"}))
        self.assertEqual((result.returncode, result.stdout), (0, "[] Nandu\n"))

    def test_crlf_in_the_template_stays_crlf(self):
        template = self._file("t.txt", "a\r\n{% for x in xs %}{{ x }}\r\n{% endfor %}\rz")
        result = _run_bytes("render", template, self._json({"xs": [1, 2]}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "a\r\n1\r\n2\r\n\rz".encode("utf-8"))

    def test_empty_result_writes_nothing(self):
        template = self._file("t.txt", "{% if missing %}x{% endif %}")
        result = _run_bytes("render", template, self._json({}))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_template_error_exits_1_with_line_and_column(self):
        template = self._file("t.txt", "line one\n  {{ nick }}")
        result = _run("render", template, self._json({}))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "2:3: name 'nick' is not defined\n")

    def test_syntax_error_exits_1_and_a_carriage_return_is_a_column(self):
        template = self._file("t.txt", "a\r{% if x %}")
        result = _run("render", template, self._json({"x": 1}))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "1:3: 'if' is never closed with 'endif'\n")

    def test_missing_files_exit_2(self):
        missing = str(self.dir / "nope.txt")
        result = _run("render", missing, self._json({}))
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{PREFIX}{missing}: "), result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        template = self._file("t.txt", "x")
        result = _run("render", template, missing)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{PREFIX}{missing}: "), result.stderr)

    def test_a_directory_is_unreadable(self):
        result = _run("render", str(self.dir), self._json({}))
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{PREFIX}{self.dir}: "), result.stderr)

    def test_files_that_are_not_utf8_exit_2(self):
        bad = self._file("bad.txt", b"caf\xe9")
        result = _run("render", bad, self._json({}))
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{PREFIX}{bad}: not valid UTF-8"), result.stderr)
        template = self._file("t.txt", "x")
        result = _run("render", template, bad)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not valid UTF-8", result.stderr)

    def test_invalid_json_exits_2(self):
        template = self._file("t.txt", "x")
        bad = self._file("bad.json", "{'a': 1}")
        result = _run("render", template, bad)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith(f"{PREFIX}{bad}: invalid JSON"), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_json_that_is_not_an_object_exits_2(self):
        template = self._file("t.txt", "x")
        for value in ([1, 2], "text", 3, None):
            with self.subTest(value=value):
                path = self._json(value)
                result = _run("render", template, path)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(
                    result.stderr.startswith(f"{PREFIX}{path}: not a JSON object"), result.stderr
                )

    def test_wrong_argument_count_exits_2(self):
        template = self._file("t.txt", "x")
        result = _run("render", template)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_json_with_a_lone_surrogate_exits_2(self):
        template = self._file("t.txt", "{{ x }}")
        # json.dumps writes each surrogate as a "\\udxxx" escape: valid JSON, no valid text.
        for context in ({"x": "\ud800"}, {"x": "ok", "y": ["a", {"z": "b\udfff"}]},
                        {"\udc80": 1}):
            with self.subTest(context=context):
                path = self._json(context)
                result = _run("render", template, path)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertTrue(
                    result.stderr.startswith(f"{PREFIX}{path}: holds a lone surrogate '\\ud"),
                    result.stderr,
                )
                self.assertNotIn("Traceback", result.stderr)

    def test_json_with_a_surrogate_pair_is_one_character(self):
        template = self._file("t.txt", "{{ x }}")
        path = self._file("pair.json", '{"x": "\\ud83d\\ude00"}')
        result = _run("render", template, path)
        self.assertEqual((result.returncode, result.stdout), (0, "\U0001F600"))

    def test_stdout_that_cannot_encode_the_result_exits_2(self):
        args = argparse.Namespace(
            template_file=self._file("t.txt", "caf\u00e9"), json_file=self._json({})
        )
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = render_cli._run(args)
        stdout.flush()
        self.assertEqual(code, 2)
        self.assertEqual(stdout.buffer.getvalue(), b"")
        self.assertEqual(stderr.getvalue(), f"{PREFIX}stdout: cannot encode '\u00e9' as ascii\n")

    def test_deeply_nested_blocks_render(self):
        depth = 500
        template = self._file(
            "t.txt", "{% for x in l %}{% if x %}" * depth + "!" + "{% endif %}{% endfor %}" * depth
        )
        result = _run("render", template, self._json({"l": [1]}))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "!", ""))

    def test_help_lists_render_under_tools(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        tools = result.stdout.split("\ntools:\n", 1)[1]
        self.assertIn("render", tools)


if __name__ == "__main__":
    unittest.main()
