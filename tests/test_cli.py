"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan task T2.6).

The expected command set is computed here from the phase 1 public-function definition,
independently of the CLI's own discovery code, and every command is run once in a real
subprocess with ``sys.executable -m textkit``.
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
from typing import Any, Callable, Dict, List

import textkit
from textkit.__main__ import _main

# A text that every current command does something visible with: spaces to squeeze,
# accents to strip or drop, case boundaries, separators, an apostrophe and punctuation.
SAMPLE = "  Héllo_wörld-Foo  barBaz, don't!  "

# Fixed so argparse wraps --help the same way on every terminal; UTF-8 so non-ASCII
# results decode the same way whatever the locale of the machine running the tests.
ENV = dict(os.environ, COLUMNS="80", PYTHONIOENCODING="utf-8")
# The repository root, so that `-m textkit` finds this checkout wherever the tests run from.
ROOT = pathlib.Path(__file__).resolve().parents[1]


def expected_commands() -> Dict[str, Callable[..., Any]]:
    """Public functions (phase 1 definition) of their own module with one required parameter."""
    found = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            required = [
                p
                for p in inspect.signature(func).parameters.values()
                if p.default is p.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            if len(required) == 1:
                found[name] = func
    return found


def expected_output(result: Any) -> str:
    """The output rule of T2.6, restated: JSON for dict and list, print() for the rest."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


def run_cli(*args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``python -m textkit`` with ``args`` and capture its output as UTF-8 text."""
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=ENV,
        cwd=ROOT,
        check=False,
    )


def help_commands(help_text: str) -> List[str]:
    """Command names listed in ``--help``: argparse indents each subcommand by 4 spaces."""
    return re.findall(r"^    (\w+)", help_text, re.M)


class MainTest(unittest.TestCase):
    """``_main`` through ``python3 -m textkit``, plus a few in-process calls."""

    def test_help_lists_exactly_the_computed_commands(self) -> None:
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = expected_commands()
        self.assertTrue(expected, "no command discovered: the test would prove nothing")
        self.assertEqual(sorted(help_commands(proc.stdout)), sorted(expected))

    def test_help_shows_the_first_docstring_line_of_every_command(self) -> None:
        proc = run_cli("--help")
        # argparse re-wraps help lines, so compare with whitespace collapsed.
        flat = " ".join(proc.stdout.split())
        for name, func in expected_commands().items():
            with self.subTest(command=name):
                first = inspect.getdoc(func).splitlines()[0]
                self.assertIn(" ".join(first.split()), flat)

    def test_every_command_runs_once(self) -> None:
        for name, func in expected_commands().items():
            with self.subTest(command=name):
                proc = run_cli(name, SAMPLE)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout, expected_output(func(SAMPLE)))
                self.assertEqual(proc.stderr, "")

    def test_output_formats(self) -> None:
        # One command per output rule present today: str as is, int with print(), dict as
        # sorted JSON that keeps non-ASCII characters.
        self.assertEqual(run_cli("slugify", "Hello, World!").stdout, "hello-world\n")
        self.assertEqual(run_cli("word_count", "one two three").stdout, "3\n")
        self.assertEqual(run_cli("char_freq", "ñba").stdout, '{"a": 1, "b": 1, "ñ": 1}\n')

    def test_bool_and_list_results_use_their_rules(self) -> None:
        # No current command returns a bool or a list, so check the rules in-process.
        from textkit.__main__ import _format

        self.assertEqual(_format(True), "True")
        self.assertEqual(_format(["b", "á"]), '["b", "á"]')

    def test_no_arguments_prints_usage_to_stderr_and_exits_2(self) -> None:
        proc = run_cli()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_unknown_function_exits_2(self) -> None:
        proc = run_cli("no_such_function", "text")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("invalid choice", proc.stderr)

    def test_function_with_two_required_parameters_is_not_a_command(self) -> None:
        # truncate(text, width) needs two arguments, so the CLI must reject it.
        proc = run_cli("truncate", "text")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)

    def test_wrong_argument_count_exits_2(self) -> None:
        for args in (["slugify"], ["slugify", "a", "b"]):
            with self.subTest(args=args):
                proc = run_cli(*args)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")
                self.assertIn("usage:", proc.stderr)

    def test_double_dash_passes_a_text_that_starts_with_a_dash(self) -> None:
        proc = run_cli("squeeze", "--", "-x   y")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "-x y\n")

    def test_in_process_call_returns_the_exit_status(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(_main(["squeeze", "  a   b "]), 0)
            self.assertEqual(_main([]), 2)
        self.assertEqual(out.getvalue(), "a b\n")
        self.assertIn("usage:", err.getvalue())

    def test_import_has_no_side_effects(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            capture_output=True,
            text=True,
            env=ENV,
            cwd=ROOT,
            check=False,
        )
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))


class VersionTest(unittest.TestCase):
    """``python3 -m textkit --version`` and ``textkit.__version__`` (plan task T2.7)."""

    def test_version_flag_prints_the_package_version_and_exits_0(self) -> None:
        proc = run_cli("--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, f"textkit {textkit.__version__}\n")
        self.assertEqual(proc.stderr, "")

    def test_package_version_is_0_1_0(self) -> None:
        self.assertEqual(textkit.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
