"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (T2.6, T2.7).

Nothing here names a real textkit function: the expected command set is recomputed from the
public-function definition (phase 1 "Rules for every task"), every command is run once with
a generic argument, and the conversion, ``--``, output and error paths use stub functions
patched in for ``textkit.__main__._commands`` (no file is written under ``textkit/``). So
functions added later (phase 3 included) need no edit here.
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
import typing
import unittest
from unittest import mock

import textkit
import textkit.__main__
from textkit.__main__ import _main

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Stub commands, patched in for _commands(): they exercise every CLI rule without depending
# on any real textkit function.
def stub_double(n: int) -> int:
    """Return twice n."""
    return 2 * n


def stub_raise(text: str) -> str:
    """Raise the exception named by text."""
    if text == "value":
        raise ValueError("bad value")
    if text == "key":
        raise KeyError("missing")
    if text == "type":
        raise TypeError("bad type")
    raise RuntimeError("unexpected")


def stub_echo(text: str) -> str:
    """Return text unchanged (100% as is)."""
    return text


def stub_dict(text: str) -> dict:
    """Return a dict with unsorted keys."""
    return {"b": text, "a": 1}


def stub_list(text: str) -> list:
    """Return a list."""
    return [text, 2]


def stub_bool(text: str) -> bool:
    """Return whether text is empty."""
    return text == ""


def stub_default(text: str, times: int = 2) -> str:
    """Repeat text, keeping the default."""
    return text * times


STUBS = {f.__name__: f for f in (stub_double, stub_raise, stub_echo, stub_dict, stub_list, stub_bool, stub_default)}


def _expected_commands() -> dict:
    """Name -> function for every public function with exactly one required parameter."""
    commands = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or function.__module__ != module.__name__:
                continue
            required = [
                p
                for p in inspect.signature(function).parameters.values()
                if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            if len(required) == 1:
                commands.setdefault(name, (function, required[0]))
    return commands


def _run(*args: str) -> subprocess.CompletedProcess:
    """Run the real entry point in a subprocess, from the repository root."""
    env = dict(os.environ, COLUMNS="1000")  # no wrapping in --help
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def _help_commands(help_text: str) -> dict:
    """Parse the sub-command list of ``--help``: name -> help line.

    argparse indents each sub-command by 4 spaces; a long name puts its help on the next,
    more indented line.
    """
    lines = help_text.splitlines()
    found = {}
    for i, line in enumerate(lines):
        match = re.match(r"^ {4}(\S+)(.*)$", line)
        if match:
            text = match.group(2).strip()
            if not text and i + 1 < len(lines) and lines[i + 1].startswith(" " * 5):
                text = lines[i + 1].strip()
            found[match.group(1)] = text
    return found


def _call(*argv: str):
    """Run ``_main`` in-process; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = _main(list(argv))
        except SystemExit as exit_:  # argparse's exits, should _main ever let one through
            code = exit_.code
    return code, out.getvalue(), err.getvalue()


class StubCommandsMixin:
    """Replaces the discovered commands with STUBS for one test case."""

    def setUp(self):
        patcher = mock.patch.object(textkit.__main__, "_commands", return_value=dict(STUBS))
        patcher.start()
        self.addCleanup(patcher.stop)


class CommandListTest(unittest.TestCase):
    def test_help_lists_exactly_the_discovered_commands(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = _expected_commands()
        listed = _help_commands(result.stdout)
        self.assertEqual(set(listed), set(expected))
        for name, (function, _) in expected.items():
            first_line = next(iter((inspect.getdoc(function) or "").splitlines()), "")
            with self.subTest(command=name):
                self.assertEqual(listed[name], " ".join(first_line.split()))

    def test_commands_follows_the_public_function_definition(self):
        self.assertEqual(set(textkit.__main__._commands()), set(_expected_commands()))

    def test_there_is_at_least_one_command(self):
        self.assertTrue(_expected_commands())


class CommandRunTest(unittest.TestCase):
    def test_every_command_runs_once(self):
        for name, (function, parameter) in sorted(_expected_commands().items()):
            hint = typing.get_type_hints(function).get(parameter.name, parameter.annotation)
            argument = "1" if hint is int else "a"
            with self.subTest(command=name, argument=argument):
                result = _run(name, argument)
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_import_has_no_side_effects(self):
        result = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


class UsageErrorTest(unittest.TestCase):
    def test_no_arguments_prints_usage_and_exits_2(self):
        result = _run()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unknown_function_exits_2(self):
        result = _run("no_such_function", "a")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no_such_function", result.stderr)

    def test_private_function_is_unknown(self):
        code, _, err = _call("_main", "a")
        self.assertEqual(code, 2)
        self.assertIn("invalid choice", err)

    def test_missing_argument_exits_2(self):
        name = sorted(_expected_commands())[0]
        code, out, err = _call(name)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("required", err)

    def test_two_arguments_exit_2(self):
        name = sorted(_expected_commands())[0]
        code, out, err = _call(name, "a", "b")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unrecognized arguments", err)


class StubHelpTest(StubCommandsMixin, unittest.TestCase):
    def test_help_lists_every_patched_command(self):
        code, out, _ = _call("--help")
        self.assertEqual(code, 0)
        self.assertEqual(set(_help_commands(out)), set(STUBS))

    def test_percent_in_docstring_is_shown_literally(self):
        _, out, _ = _call("--help")
        self.assertEqual(_help_commands(out)["stub_echo"], "Return text unchanged (100% as is).")

    def test_parameter_with_default_keeps_it(self):
        self.assertEqual(_call("stub_default", "ab"), (0, "abab\n", ""))


class OutputFormatTest(StubCommandsMixin, unittest.TestCase):
    def test_str_is_printed_as_is(self):
        self.assertEqual(_call("stub_echo", "Ñandú  x"), (0, "Ñandú  x\n", ""))

    def test_bool_is_printed(self):
        self.assertEqual(_call("stub_bool", ""), (0, "True\n", ""))

    def test_int_is_printed(self):
        self.assertEqual(_call("stub_double", "21"), (0, "42\n", ""))

    def test_dict_is_sorted_json_without_ascii_escapes(self):
        code, out, _ = _call("stub_dict", "ñ")
        self.assertEqual((code, out), (0, '{"a": 1, "b": "ñ"}\n'))
        self.assertEqual(json.loads(out), {"a": 1, "b": "ñ"})

    def test_list_is_json(self):
        self.assertEqual(_call("stub_list", "x"), (0, '["x", 2]\n', ""))


class ArgumentConversionTest(StubCommandsMixin, unittest.TestCase):
    def test_integer_arguments_are_converted(self):
        for argument, printed in (("5", "10\n"), ("-3", "-6\n"), ("007", "14\n"), ("0", "0\n")):
            with self.subTest(argument=argument):
                self.assertEqual(_call("stub_double", argument), (0, printed, ""))

    def test_non_integer_arguments_exit_2(self):
        # "٣" (Arabic-Indic three), "+5", " 5", "5\n" and "1_0" are all accepted by int().
        for argument in ("x", "1.5", "", "+5", " 5", "5\n", "1_0", "٣", "--5"):
            with self.subTest(argument=argument):
                code, out, err = _call("stub_double", "--", argument)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("usage:", err)
                self.assertNotIn("Traceback", err)

    def test_digits_then_letters_exit_2(self):
        code, out, err = _call("stub_double", "1a")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("expected an integer", err)

    @unittest.skipUnless(hasattr(sys, "set_int_max_str_digits"), "no int digit limit here")
    def test_value_error_from_int_exits_2(self):
        # A matching argument that int() still rejects: more digits than the limit allows.
        self.addCleanup(sys.set_int_max_str_digits, sys.get_int_max_str_digits())
        sys.set_int_max_str_digits(640)
        code, out, err = _call("stub_double", "1" * 1000)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("usage:", err)
        self.assertNotIn("Traceback", err)

    def test_double_dash_passes_a_leading_dash_argument(self):
        self.assertEqual(_call("stub_echo", "--", "-x"), (0, "-x\n", ""))

    def test_leading_dash_without_double_dash_exits_2(self):
        code, _, _ = _call("stub_echo", "-x")
        self.assertEqual(code, 2)

    def test_text_parameters_are_not_converted(self):
        self.assertEqual(_call("stub_echo", "12"), (0, "12\n", ""))


class FunctionErrorTest(StubCommandsMixin, unittest.TestCase):
    def test_value_key_and_type_errors_exit_1(self):
        for argument, message in (
            ("value", "error: bad value\n"),
            ("key", "error: 'missing'\n"),
            ("type", "error: bad type\n"),
        ):
            with self.subTest(argument=argument):
                self.assertEqual(_call("stub_raise", argument), (1, "", message))

    def test_unprintable_result_exits_1(self):
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
        err = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(err):
            code = _main(["stub_echo", "Ñandú"])
        self.assertEqual(code, 1)
        self.assertTrue(err.getvalue().startswith("error: "), err.getvalue())

    def test_other_exceptions_propagate(self):
        # Only the three documented exceptions are user errors; anything else is a bug.
        with self.assertRaises(RuntimeError):
            _call("stub_raise", "other")


class VersionTest(unittest.TestCase):
    """``--version`` (T2.7): the version comes from ``textkit.__version__`` only."""

    def test_version_option_prints_the_package_version(self):
        result = _run("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"textkit {textkit.__version__}\n")
        self.assertEqual(result.stderr, "")

    def test_package_version_is_0_1_0(self):
        self.assertEqual(textkit.__version__, "0.1.0")

    def test_version_string_is_written_only_in_init(self):
        # __main__.py must read textkit.__version__, not repeat the literal.
        files = [
            path.relative_to(ROOT).as_posix()
            for path in sorted((ROOT / "textkit").rglob("*.py"))
            if textkit.__version__ in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(files, ["textkit/__init__.py"])


if __name__ == "__main__":
    unittest.main()
