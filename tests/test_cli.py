"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan tasks T2.6, T2.7).

The expected command set is computed here from the public-function definition of the phase 1
rules, independently of the discovery code in ``textkit/__main__.py``: public functions are
read with ``ast`` from the sources (as ``scripts/check.sh`` does), then kept when they have
exactly one parameter without a default. Every command is also run once in a subprocess with
``sys.executable -m textkit``, so a function added later is exercised with no test change.
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
import types
import unittest
from typing import Any, Dict, List, Tuple
from unittest import mock

import textkit
import textkit.__main__ as cli

ROOT = pathlib.Path(__file__).resolve().parents[1]

# One text that gives every current command something to do: case changes, separators,
# accents, repeated characters and several words.
SAMPLE = "Hello, Wörld  naïve_user-id HTTPServer"


def _public_functions() -> Dict[str, Any]:
    """Name -> function for every public function, by the phase 1 definition."""
    found = {}
    for path in sorted((ROOT / "textkit").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{path.stem}")
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                found[node.name] = getattr(module, node.name)
    return found


def _expected_commands() -> Dict[str, Any]:
    """The public functions with exactly one parameter without a default."""
    variadic = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    return {
        name: f
        for name, f in _public_functions().items()
        if sum(
            p.kind not in variadic and p.default is inspect.Parameter.empty
            for p in inspect.signature(f).parameters.values()
        )
        == 1
    }


def _expected_output(result: Any) -> str:
    """What the CLI must print for ``result``, written from the T2.6 output rules."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    if isinstance(result, (str, bool, int)):
        return f"{result}\n"
    raise AssertionError(f"no output rule for a {type(result).__name__} result")


def _run(*args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``python3 -m textkit <args>`` from the repository root, UTF-8 on both ends."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def _main_captured(argv: List[str]) -> Tuple[int, str, str]:
    """Call ``cli._main(argv)`` in process; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli._main(argv)
    return code, out.getvalue(), err.getvalue()


def _help_commands(help_text: str) -> Dict[str, str]:
    """Parse the ``commands:`` block of ``--help`` into name -> summary."""
    lines = help_text.splitlines()
    start = lines.index("commands:") + 1
    rows = {}
    for line in lines[start:]:
        if not line.strip():
            break
        name, _, summary = line.strip().partition(" ")
        rows[name] = summary.strip()
    return rows


def _fake_module(name: str, source: str) -> types.ModuleType:
    """A module object built from ``source``; its functions get ``__module__ == name``."""
    module = types.ModuleType(name)
    exec(source, module.__dict__)
    return module


class MainTest(unittest.TestCase):
    """``_main`` and ``python3 -m textkit`` end to end."""

    def test_help_lists_exactly_the_public_one_text_functions(self) -> None:
        code, out, err = _main_captured(["--help"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        expected = _expected_commands()
        rows = _help_commands(out)
        self.assertEqual(set(rows), set(expected))
        for name, f in expected.items():
            doc = inspect.getdoc(f) or ""
            first_line = doc.splitlines()[0].strip() if doc else ""
            self.assertEqual(rows[name], first_line, name)

    def test_help_via_subprocess(self) -> None:
        proc = _run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(set(_help_commands(proc.stdout)), set(_expected_commands()))

    def test_every_command_runs_once_via_subprocess(self) -> None:
        commands = _expected_commands()
        self.assertTrue(commands, "no command discovered")
        for name, f in commands.items():
            with self.subTest(command=name):
                proc = _run(name, SAMPLE)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(proc.stdout, _expected_output(f(SAMPLE)))

    def test_known_outputs(self) -> None:
        self.assertEqual(_run("slugify", "Hello, World!").stdout, "hello-world\n")
        self.assertEqual(_run("word_count", "well-known R2-D2").stdout, "2\n")
        # JSON with sorted keys and non-ASCII kept as is.
        self.assertEqual(_run("char_freq", "baé b").stdout, '{"a": 1, "b": 2, "é": 1}\n')

    def test_no_arguments_prints_usage_to_stderr_and_exits_2(self) -> None:
        proc = _run()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_unknown_function_exits_2(self) -> None:
        proc = _run("no_such_function", "x")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("invalid choice", proc.stderr)

    def test_function_with_two_required_parameters_is_not_a_command(self) -> None:
        # wrap(text, width) needs two arguments, so it is an unknown function here.
        code, out, err = _main_captured(["wrap", "a b"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("invalid choice", err)

    def test_wrong_argument_count_exits_2(self) -> None:
        for argv in (["slugify"], ["slugify", "a", "b"]):
            with self.subTest(argv=argv):
                code, out, err = _main_captured(argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn("usage:", err)

    def test_output_formats_and_value_error(self) -> None:
        fake = _fake_module(
            "textkit.fake",
            "def as_str(text): return text.upper()\n"
            "def as_bool(text): return text == 'yes'\n"
            "def as_int(text): return len(text)\n"
            "def as_list(text): return list(text)\n"
            "def as_dict(text): return {'z': 1, 'ñ': 2, 'a': [text]}\n"
            "def fails(text): raise ValueError('bad text')\n",
        )
        with mock.patch.object(cli, "_textkit_modules", return_value=[fake]):
            cases = [
                ("as_str", "ab", "AB\n"),
                ("as_bool", "yes", "True\n"),
                ("as_int", "abc", "3\n"),
                ("as_list", "añ", '["a", "ñ"]\n'),
                ("as_dict", "x", '{"a": ["x"], "z": 1, "ñ": 2}\n'),
            ]
            for name, text, expected in cases:
                with self.subTest(command=name):
                    self.assertEqual(_main_captured([name, text]), (0, expected, ""))
            code, out, err = _main_captured(["fails", "x"])
            self.assertEqual((code, out), (1, ""))
            self.assertIn("bad text", err)

    def test_import_has_no_side_effects(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            importlib.reload(cli)
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))


class CommandsTest(unittest.TestCase):
    """``_commands``: run-time discovery of the commands."""

    def test_discovery_matches_the_public_function_definition(self) -> None:
        self.assertEqual(cli._commands(cli._textkit_modules()), _expected_commands())

    def test_private_modules_are_skipped(self) -> None:
        names = [m.__name__ for m in cli._textkit_modules()]
        self.assertNotIn("textkit.__main__", names)
        self.assertTrue(all(not n.split(".")[-1].startswith("_") for n in names))

    def test_filters(self) -> None:
        fake = _fake_module(
            "textkit.fake",
            "from json import dumps\n"  # imported, so not a function of this module
            "def one(text): return text\n"
            "def with_default(text, n=3): return text * n\n"
            "def keyword_only(*, text): return text\n"
            "def variadic(text, *args, **kwargs): return text\n"
            "def two(text, width): return text\n"
            "def none(): return ''\n"
            "def _private(text): return text\n",
        )
        self.assertEqual(
            list(cli._commands([fake])), ["keyword_only", "one", "variadic", "with_default"]
        )

    def test_defaults_are_kept_and_keyword_only_is_bound_by_name(self) -> None:
        fake = _fake_module(
            "textkit.fake",
            "def with_default(text, n=3): return text * n\n"
            "def keyword_only(*, text): return text + '!'\n",
        )
        with mock.patch.object(cli, "_textkit_modules", return_value=[fake]):
            self.assertEqual(_main_captured(["with_default", "ab"]), (0, "ababab\n", ""))
            self.assertEqual(_main_captured(["keyword_only", "hi"]), (0, "hi!\n", ""))

    def test_duplicate_command_names_raise(self) -> None:
        a = _fake_module("textkit.a", "def same(text): return text\n")
        b = _fake_module("textkit.b", "def same(text): return text\n")
        with self.assertRaises(RuntimeError):
            cli._commands([a, b])



class VersionTest(unittest.TestCase):
    """``python3 -m textkit --version`` (plan task T2.7)."""

    def test_version_flag_prints_the_package_version(self) -> None:
        proc = _run("--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.stdout, f"textkit {textkit.__version__}\n")

    def test_package_version(self) -> None:
        self.assertEqual(textkit.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
