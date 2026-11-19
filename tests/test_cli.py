"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan task T2.6).

The expected commands are computed here from the public-function definition of
docs/phases/phase-1-core-helpers.md, independently of the CLI's own discovery, so that a
function added to any module by another task is covered with no change to this file.
"""

import contextlib
import importlib
import inspect
import io
import json
import os
import pathlib
import pkgutil
import re
import subprocess
import sys
import unittest

import textkit
from textkit.__main__ import _commands, _format, _main

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
# Any text works for every current command; it mixes cases, separators, punctuation and a
# non-ASCII letter so the outputs are not trivial.
SAMPLE_TEXT = "Hello, naïve World_wide-web 42"


def _expected_commands() -> dict:
    """Return name -> function for every public function with one parameter without default."""
    expected = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in vars(module).items():
            if name.startswith("_") or not inspect.isfunction(func):
                continue
            if func.__module__ != module.__name__:
                continue
            required = [
                p
                for p in inspect.signature(func).parameters.values()
                if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            if len(required) == 1:
                expected[name] = func
    return expected


def _expected_output(result: object) -> str:
    """Return what the CLI must print for ``result``, per the T2.6 output rules."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run ``sys.executable -m textkit *args`` from the repository root, UTF-8, fixed width."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", COLUMNS="100", NO_COLOR="1")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _main_in_process(*args: str) -> tuple:
    """Call ``_main(list(args))`` capturing stdout and stderr; return (status, out, err)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = _main(list(args))
    return status, out.getvalue(), err.getvalue()


def _help_commands(help_text: str) -> list:
    """Return the command names listed under "commands:" in the ``--help`` output."""
    section = help_text.split("\ncommands:\n", 1)[1].split("\n\n", 1)[0]
    # A command line is indented by exactly four spaces; wrapped help lines by more.
    return re.findall(r"^ {4}(\w+)", section, re.M)


class MainTest(unittest.TestCase):
    """The ``python3 -m textkit`` entry point, ``_main``."""

    def test_discovery_matches_the_public_function_definition(self):
        self.assertEqual(set(_commands()), set(_expected_commands()))
        self.assertIn("slugify", _commands())
        # Functions with a second required parameter are not commands.
        self.assertNotIn("truncate", _commands())
        self.assertNotIn("wrap", _commands())

    def test_help_lists_every_command_with_its_docstring_summary(self):
        proc = _run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        listed = _help_commands(proc.stdout)
        self.assertEqual(sorted(listed), sorted(set(listed)), "a command is listed twice")
        self.assertEqual(set(listed), set(_expected_commands()))
        flat = " ".join(proc.stdout.split())  # undo argparse's line wrapping
        for name, func in _expected_commands().items():
            summary = (inspect.getdoc(func) or "").splitlines()[0].strip()
            self.assertIn(" ".join(summary.split()), flat, name)

    def test_every_command_runs_once_via_subprocess(self):
        for name, func in sorted(_expected_commands().items()):
            with self.subTest(command=name):
                proc = _run_cli(name, SAMPLE_TEXT)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, _expected_output(func(SAMPLE_TEXT)))
                self.assertEqual(proc.stderr, "")

    def test_output_formats(self):
        self.assertEqual(_main_in_process("slugify", "Hello, World!"), (0, "hello-world\n", ""))
        self.assertEqual(_main_in_process("word_count", "one two three"), (0, "3\n", ""))
        # dict: JSON with sorted keys, non-ASCII kept as is.
        self.assertEqual(_main_in_process("char_freq", "ñba"), (0, '{"a": 1, "b": 1, "ñ": 1}\n', ""))
        # No current command returns a list or a bool: check the formatter directly.
        self.assertEqual(_format(["b", "ñ"]), '["b", "ñ"]')
        self.assertEqual(_format({"b": 1, "a": [2]}), '{"a": [2], "b": 1}')
        self.assertEqual(_format(True), "True")
        self.assertEqual(_format(0), "0")
        self.assertEqual(_format("as is "), "as is ")

    def test_unknown_function_exits_2_on_stderr(self):
        status, out, err = _main_in_process("no_such_function", "x")
        self.assertEqual((status, out), (2, ""))
        self.assertIn("invalid choice", err)

    def test_private_and_non_text_functions_are_not_commands(self):
        for name in ("_main", "_words", "truncate"):
            with self.subTest(name=name):
                status, out, _ = _main_in_process(name, "x")
                self.assertEqual((status, out), (2, ""))

    def test_wrong_argument_count_exits_2_on_stderr(self):
        for args in (("slugify",), ("slugify", "a", "b")):
            with self.subTest(args=args):
                status, out, err = _main_in_process(*args)
                self.assertEqual((status, out), (2, ""))
                self.assertIn("usage:", err)

    def test_no_arguments_prints_usage_and_exits_2(self):
        status, out, err = _main_in_process()
        self.assertEqual((status, out), (2, ""))
        self.assertIn("usage:", err)
        proc = _run_cli()
        self.assertEqual((proc.returncode, proc.stdout), (2, ""))
        self.assertIn("usage:", proc.stderr)

    def test_text_starting_with_a_dash_after_double_dash(self):
        self.assertEqual(_main_in_process("squeeze", "--", "-a  b"), (0, "-a b\n", ""))

    def test_importing_the_module_has_no_side_effects(self):
        code = "import textkit.__main__"
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd=REPO_ROOT, capture_output=True, text=True,
            check=False,
        )
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
