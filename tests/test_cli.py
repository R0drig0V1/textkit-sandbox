"""Tests for the command line, ``textkit/__main__.py`` (plan task T2.6).

The expected command set is computed here from the public-function definition of phase 1,
independently of ``textkit.__main__``, so a discovery bug there cannot hide behind the same
bug in the test. Every command is run once through ``sys.executable -m textkit``.
"""

import contextlib
import importlib
import inspect
import io
import json
import os
import pathlib
import pkgutil
import subprocess
import sys
import unittest
from typing import Any, Callable, Dict, List
from unittest import mock

import textkit
from textkit import __main__ as cli

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# A text that gives every current command something to do: case changes, separators,
# punctuation, repeated letters, an accent and runs of whitespace.
SAMPLE = "Héllo,  wörld_fooBar-baz 42"


def expected_commands() -> Dict[str, Callable[..., Any]]:
    """Public functions (phase 1 definition) with exactly one parameter without a default."""
    found = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            required = [
                p for p in inspect.signature(func).parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (inspect.Parameter.VAR_POSITIONAL,
                                   inspect.Parameter.VAR_KEYWORD)
            ]
            if len(required) == 1:
                found[name] = func
    return found


def expected_output(result: Any) -> str:
    """The stdout the plan specifies for ``result``, newline included."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


def run_cli(args: List[str]) -> subprocess.CompletedProcess:
    """Run ``python -m textkit <args>`` from the repository root, decoding UTF-8."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
        check=False,
    )


def help_commands(help_text: str) -> Dict[str, str]:
    """Parse the ``commands:`` block of ``--help`` into {name: summary}."""
    lines = help_text.splitlines()
    start = lines.index("commands:") + 1
    listed = {}
    for line in lines[start:]:
        if not line.strip():
            break
        name, _, summary = line.strip().partition(" ")
        listed[name] = summary.strip()
    return listed


class MainTest(unittest.TestCase):
    def test_discovery_matches_the_public_function_definition(self):
        commands = expected_commands()
        # Sanity: one-argument functions are in, functions needing more are out.
        self.assertIn("slugify", commands)
        self.assertIn("word_count", commands)
        self.assertNotIn("truncate", commands)
        self.assertNotIn("wrap", commands)
        self.assertEqual(set(cli._commands()), set(commands))

    def test_help_lists_every_command_with_its_first_docstring_line(self):
        proc = run_cli(["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        listed = help_commands(proc.stdout)
        commands = expected_commands()
        self.assertEqual(set(listed), set(commands))
        for name, func in commands.items():
            first_line = inspect.getdoc(func).splitlines()[0]
            self.assertEqual(listed[name], first_line, name)

    def test_every_command_runs_once(self):
        for name, func in sorted(expected_commands().items()):
            with self.subTest(command=name):
                proc = run_cli([name, SAMPLE])
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(proc.stdout, expected_output(func(SAMPLE)))

    def test_known_outputs(self):
        self.assertEqual(run_cli(["slugify", "Hello, World!"]).stdout, "hello-world\n")
        self.assertEqual(run_cli(["word_count", "one two three"]).stdout, "3\n")
        # dict: JSON with sorted keys and non-ASCII kept as is.
        self.assertEqual(run_cli(["char_freq", "baÑa"]).stdout,
                         '{"a": 2, "b": 1, "Ñ": 1}\n')

    def test_text_starting_with_dash_after_double_dash(self):
        self.assertEqual(run_cli(["slugify", "--", "-Hi-"]).stdout, "hi\n")

    def test_no_arguments_prints_usage_on_stderr_and_exits_2(self):
        proc = run_cli([])
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_unknown_function_exits_2(self):
        proc = run_cli(["no_such_function", "x"])
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("no_such_function", proc.stderr)

    def test_private_and_multi_argument_functions_are_not_commands(self):
        for name in ("truncate", "_words", "_main"):
            with self.subTest(name=name):
                proc = run_cli([name, "x"])
                self.assertEqual(proc.returncode, 2)
                self.assertIn("invalid choice", proc.stderr)

    def test_wrong_argument_count_exits_2(self):
        for args in (["slugify"], ["slugify", "a", "b"]):
            with self.subTest(args=args):
                proc = run_cli(args)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")
                self.assertIn("error:", proc.stderr)

    def test_main_in_process(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(cli._main(["squeeze", "  a   b "]), 0)
            self.assertEqual(cli._main([]), 2)
        self.assertEqual(out.getvalue(), "a b\n")
        self.assertIn("usage:", err.getvalue())

    def test_value_error_exits_1_with_message_on_stderr(self):
        def picky(text: str) -> str:
            """Reject everything."""
            raise ValueError(f"cannot handle {text!r}")

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "_commands", return_value={"picky": picky}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(cli._main(["picky", "x"]), 1)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "textkit: error: cannot handle 'x'\n")

    def test_output_formats(self):
        self.assertEqual(cli._format("a b"), "a b")
        self.assertEqual(cli._format(True), "True")
        self.assertEqual(cli._format(3), "3")
        self.assertEqual(cli._format({"b": 1, "á": 2}), '{"b": 1, "á": 2}')
        self.assertEqual(cli._format(["x", "ñ"]), '["x", "ñ"]')

    def test_parameters_with_defaults_keep_their_default(self):
        def with_default(text: str, times: int = 2) -> str:
            """Repeat text."""
            return text * times

        out = io.StringIO()
        with mock.patch.object(cli, "_commands", return_value={"with_default": with_default}), \
                contextlib.redirect_stdout(out):
            self.assertEqual(cli._main(["with_default", "ab"]), 0)
        self.assertEqual(out.getvalue(), "abab\n")

    def test_import_has_no_side_effects(self):
        proc = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))


if __name__ == "__main__":
    unittest.main()
