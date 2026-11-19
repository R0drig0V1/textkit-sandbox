"""Tests for the command line, textkit/__main__.py (``python3 -m textkit``).

The expected command set is computed here independently of the code under test: public
functions are found by parsing the source of ``textkit/`` with ``ast``, the same way
``scripts/check.sh`` does, so a bug in the command line's own discovery cannot hide itself.
The end-to-end tests run the real interpreter (``sys.executable -m textkit``) through
``subprocess``.
"""

import ast
import contextlib
import importlib
import inspect
import io
import json
import os
import pathlib
import subprocess
import sys
import unittest

from textkit.__main__ import _main

ROOT = pathlib.Path(__file__).resolve().parents[1]
# A sample with capitals, punctuation, a repeated letter and an accent, so every command has
# something to do. Every current command accepts any `str`.
SAMPLE = "Hello, Wörld! hello_world"


def expected_commands() -> dict:
    """Return {name: function} for every public function of exactly one required parameter.

    Public function (docs/phases/phase-1-core-helpers.md): a top-level ``def`` whose name does
    not start with ``_``, in a module of ``textkit/`` whose name does not start with ``_``.
    """
    found = {}
    for path in sorted((ROOT / "textkit").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]
        module = importlib.import_module(f"textkit.{path.stem}")
        for name in names:
            func = getattr(module, name)
            required = [
                p
                for p in inspect.signature(func).parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            if len(required) == 1:
                found[name] = func
    return found


def expected_output(result) -> str:
    """The stdout T2.6 specifies for a function's result, newline included."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run ``python3 -m textkit`` with ``args`` from the repository root, in UTF-8."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )


def help_commands(help_text: str) -> dict:
    """Parse the ``commands:`` section of ``--help`` into {name: summary}."""
    lines = help_text.split("commands:\n", 1)[1].splitlines()
    commands = {}
    for line in lines:
        if not line.strip():
            break
        name, _, summary = line.strip().partition(" ")
        commands[name] = summary.strip()
    return commands


def call_main(*args: str):
    """Call ``_main`` in-process; return (status, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = _main(list(args))
    return status, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """End-to-end tests through ``sys.executable -m textkit``."""

    def test_help_lists_exactly_the_public_one_text_functions(self):
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        listed = help_commands(proc.stdout)
        expected = expected_commands()
        self.assertTrue(expected, "no commands discovered at all")
        self.assertEqual(set(listed), set(expected))
        for name, func in expected.items():
            with self.subTest(command=name):
                first_line = inspect.getdoc(func).splitlines()[0].strip()
                self.assertEqual(listed[name], first_line)

    def test_every_command_runs_once(self):
        for name, func in expected_commands().items():
            with self.subTest(command=name):
                proc = run_cli(name, SAMPLE)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, expected_output(func(SAMPLE)))
                self.assertEqual(proc.stderr, "")

    def test_no_arguments_prints_usage_and_exits_2(self):
        proc = run_cli()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_unknown_function_exits_2(self):
        proc = run_cli("no_such_function", "text")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("no_such_function", proc.stderr)

    def test_private_and_multi_argument_functions_are_not_commands(self):
        # `wrap(text, width)` has two parameters without a default; `_split_camel` is private.
        for name in ("wrap", "truncate", "_split_camel", "_main"):
            with self.subTest(command=name):
                self.assertEqual(run_cli(name, "text").returncode, 2)

    def test_missing_text_exits_2(self):
        proc = run_cli("word_count")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("text", proc.stderr)

    def test_extra_argument_exits_2(self):
        proc = run_cli("word_count", "one", "two")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("two", proc.stderr)

    def test_non_ascii_output_is_not_escaped(self):
        proc = run_cli("char_freq", "ñañ")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, '{"a": 1, "ñ": 2}\n')

    def test_importing_the_module_has_no_side_effects(self):
        proc = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=ROOT,
            capture_output=True,
            encoding="utf-8",
            timeout=60,
        )
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))


class InProcessMainTest(unittest.TestCase):
    """Faster checks of output formats and statuses through ``_main`` itself."""

    def test_str_is_printed_as_is(self):
        self.assertEqual(call_main("to_snake_case", "HTTPServer"), (0, "http_server\n", ""))

    def test_int_is_printed(self):
        self.assertEqual(call_main("word_count", "well-known fact"), (0, "2\n", ""))

    def test_dict_is_sorted_json(self):
        self.assertEqual(call_main("char_freq", "baA"), (0, '{"A": 1, "a": 1, "b": 1}\n', ""))

    def test_text_starting_with_dash_after_double_dash(self):
        self.assertEqual(call_main("word_count", "--", "-x y"), (0, "2\n", ""))

    def test_empty_text(self):
        self.assertEqual(call_main("word_count", ""), (0, "0\n", ""))

    def test_help_returns_0(self):
        status, out, _ = call_main("--help")
        self.assertEqual(status, 0)
        self.assertIn("commands:", out)

    def test_no_arguments_returns_2(self):
        status, out, err = call_main()
        self.assertEqual((status, out), (2, ""))
        self.assertIn("usage:", err)


if __name__ == "__main__":
    unittest.main()
