"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan task T2.6).

The expected command set is computed here from the public-function definition of
docs/phases/phase-1-core-helpers.md, independently of ``textkit.__main__``, so the test
catches a CLI that drifts from the definition; it is never a hard-coded list, so functions
merged later are covered automatically.
"""

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
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Callable, Dict, List

import textkit

ROOT = Path(__file__).resolve().parents[1]
# Exercises non-ASCII output (ensure_ascii=False) and gives every current command real work.
SAMPLE = "Ñandú camelCase_word-x"


def _expected_commands() -> Dict[str, Callable[..., Any]]:
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
                p
                for p in inspect.signature(func).parameters.values()
                if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            if len(required) == 1:
                found[name] = func
    return found


def _expected_output(result: Any) -> str:
    """The stdout the plan specifies for ``result``."""
    if isinstance(result, str):
        return result + "\n"
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


def _run(*args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``python -m textkit *args`` from the repository root, decoding UTF-8."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT), COLUMNS="80")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def _listed_commands(help_text: str) -> List[str]:
    """Command names in ``--help`` output: the lines indented by exactly four spaces."""
    return re.findall(r"^ {4}([A-Za-z_]\w*)(?:\s|$)", help_text, re.M)


class MainTest(unittest.TestCase):
    def test_import_has_no_side_effects(self) -> None:
        # A fresh interpreter: in this process another test may have imported it already.
        result = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT)),
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_expected_set_is_not_empty(self) -> None:
        # Guards the tests below against passing vacuously.
        self.assertIn("slugify", _expected_commands())
        self.assertNotIn("truncate", _expected_commands())  # `width` has no default

    def test_help_lists_exactly_the_computed_commands(self) -> None:
        result = _run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        listed = _listed_commands(result.stdout)
        self.assertEqual(len(listed), len(set(listed)), listed)
        self.assertEqual(set(listed), set(_expected_commands()))

    def test_help_shows_each_docstring_first_line(self) -> None:
        # Compared without whitespace: argparse wraps long help lines, even after a hyphen.
        flat = "".join(_run("--help").stdout.split())
        for name, func in _expected_commands().items():
            with self.subTest(command=name):
                first = inspect.getdoc(func).splitlines()[0]
                self.assertIn("".join(first.split()), flat)

    def test_every_command_runs(self) -> None:
        for name, func in sorted(_expected_commands().items()):
            with self.subTest(command=name):
                result = _run(name, SAMPLE)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, _expected_output(func(SAMPLE)))
                self.assertEqual(result.stderr, "")

    def test_output_formats(self) -> None:
        self.assertEqual(_run("slugify", "Hello, World!").stdout, "hello-world\n")
        self.assertEqual(_run("word_count", "one two").stdout, "2\n")
        self.assertEqual(_run("is_palindrome", "Anita lava la tina").stdout, "True\n")
        self.assertEqual(_run("char_freq", "bañ a").stdout, '{"a": 2, "b": 1, "ñ": 1}\n')

    def test_text_starting_with_dash_after_double_dash(self) -> None:
        self.assertEqual(_run("slugify", "--", "-Hi There").stdout, "hi-there\n")

    def test_no_arguments_exits_2_with_usage(self) -> None:
        result = _run()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("usage:", result.stderr)

    def test_unknown_function_exits_2(self) -> None:
        for name in ("no_such_function", "truncate", "_main"):
            with self.subTest(name=name):
                result = _run(name, "text")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("invalid choice", result.stderr)

    def test_wrong_argument_count_exits_2(self) -> None:
        for args in (("slugify",), ("slugify", "a", "b")):
            with self.subTest(args=args):
                result = _run(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error:", result.stderr)

    def test_main_returns_status_in_process(self) -> None:
        from textkit.__main__ import _main

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(_main(["slugify", "A b"]), 0)
            self.assertEqual(_main([]), 2)
        self.assertEqual(out.getvalue(), "a-b\n")
        self.assertIn("usage:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
