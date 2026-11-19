"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan task T2.6).

The expected command set is computed here from the plan's public-function definition, on its
own and not through the CLI's discovery code, so the two are checked against each other.
Functions are added to textkit in parallel: nothing in this file lists them by name.
"""

import contextlib
import importlib
import inspect
import io
import json
import os
import pkgutil
import re
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest import mock

import textkit
from textkit.__main__ import _main

REPO_ROOT = Path(__file__).resolve().parents[1]

# Text given to every command: letters of both cases, an accent, a separator and spaces, so
# that no command's output is trivially empty.
SAMPLE_TEXT = "Ñandú said_hello-World  twice"


def public_functions() -> Dict[str, Callable[..., Any]]:
    """Every public function: defined in a public textkit module, name without a leading ``_``."""
    functions = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and func.__module__ == module.__name__:
                functions[name] = func
    return functions


def expected_commands() -> Dict[str, Callable[..., Any]]:
    """The public functions with exactly one parameter without a default."""
    return {
        name: func
        for name, func in public_functions().items()
        if sum(
            p.default is inspect.Parameter.empty
            for p in inspect.signature(func).parameters.values()
        )
        == 1
    }


def expected_output(result: Any) -> str:
    """What the CLI must print for ``result``, by the output rules of T2.6."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


def run_cli(*args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``python3 -m textkit`` with ``args`` in a child process, from the repository root."""
    # A wide terminal keeps argparse from wrapping --help lines; UTF-8 stdio keeps accented
    # output stable whatever the locale of the machine running the tests.
    env = dict(os.environ, COLUMNS="1000", PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def run_main(argv: List[str]) -> "tuple[int, str, str]":
    """Call ``_main(argv)`` in-process; return its exit code, stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, {"COLUMNS": "1000"}):
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = _main(argv)
    return code, out.getvalue(), err.getvalue()


def help_commands(help_text: str) -> Dict[str, str]:
    """Map each command listed under "functions:" in ``--help`` to its summary line."""
    lines = help_text.split("functions:", 1)[1].splitlines()
    commands = {}
    for i, line in enumerate(lines):
        # A command line is indented by four spaces (the "function" metavar line by two).
        match = re.match(r"^ {4}(\w+)(?: +(.*))?$", line)
        if match:
            # argparse puts the summary of a name too long for its column on the next line.
            summary = match.group(2) if match.group(2) else lines[i + 1].strip()
            commands[match.group(1)] = summary
    return commands


class CliHelpTest(unittest.TestCase):
    def test_help_lists_exactly_the_computed_commands(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(help_commands(result.stdout)), set(expected_commands()))

    def test_help_shows_the_first_docstring_line(self):
        code, out, _ = run_main(["--help"])
        self.assertEqual(code, 0)
        listed = help_commands(out)
        for name, func in expected_commands().items():
            with self.subTest(command=name):
                self.assertEqual(listed[name], inspect.getdoc(func).splitlines()[0])

    def test_there_are_commands(self):
        # Guards the equality test above against both sides being empty.
        self.assertTrue(expected_commands())


class CliCommandsTest(unittest.TestCase):
    def test_every_command_runs_once(self):
        for name, func in sorted(expected_commands().items()):
            with self.subTest(command=name):
                result = run_cli(name, SAMPLE_TEXT)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected_output(func(SAMPLE_TEXT)))
                self.assertEqual(result.stderr, "")

    def test_str_is_printed_as_is(self):
        self.assertEqual(run_main(["slugify", "Hello, World!"]), (0, "hello-world\n", ""))

    def test_int_is_printed(self):
        self.assertEqual(run_main(["word_count", "one two three"]), (0, "3\n", ""))

    def test_dict_is_sorted_json_without_ascii_escapes(self):
        code, out, _ = run_main(["char_freq", "ñba"])
        self.assertEqual(code, 0)
        self.assertEqual(out, '{"a": 1, "b": 1, "ñ": 1}\n')

    def test_text_starting_with_a_dash_goes_after_double_dash(self):
        self.assertEqual(run_main(["slugify", "--", "-Hi-"]), (0, "hi\n", ""))

    def test_importing_has_no_side_effects(self):
        # A fresh interpreter that only imports the module must print nothing and exit 0.
        result = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=REPO_ROOT,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


class CliErrorsTest(unittest.TestCase):
    def test_no_arguments_prints_usage_and_exits_2(self):
        result = run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("usage:", result.stderr)

    def test_unknown_function_exits_2(self):
        result = run_cli("no_such_function", "text")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("no_such_function", result.stderr)

    def test_functions_needing_more_arguments_are_not_commands(self):
        # Public functions with two or more parameters without a default (such as a width).
        others = set(public_functions()) - set(expected_commands())
        if not others:
            self.skipTest("every public function takes one text argument")
        for name in sorted(others):
            with self.subTest(function=name):
                code, out, err = run_main([name, "a b"])
                self.assertEqual((code, out), (2, ""))
                self.assertIn("invalid choice", err)

    def test_missing_text_exits_2(self):
        code, out, err = run_main(["slugify"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("usage:", err)

    def test_extra_argument_exits_2(self):
        result = run_cli("slugify", "one", "two")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("unrecognized arguments", result.stderr)


if __name__ == "__main__":
    unittest.main()
