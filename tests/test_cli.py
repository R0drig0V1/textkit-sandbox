"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan tasks T2.6
and T2.7).

The command set is recomputed here from the public-function definition of
docs/phases/phase-1-core-helpers.md ("Rules for every task"), independently of
``textkit.__main__._commands``, so the acceptance test compares the CLI against the rule and
not against itself. Commands are run as a user would, via ``subprocess`` with
``sys.executable -m textkit``. Each run uses its own process and no shared files, so the
tests are safe to run in parallel with other checkouts.
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
from typing import Any, Callable, Dict

import textkit
from textkit.__main__ import _build_parser, _call, _format, _main

_ROOT = pathlib.Path(__file__).resolve().parents[1]
# Text every command runs on: punctuation, non-ASCII, several words and sentences.
_SAMPLE = "Ñandú says: Hello, World! It's 3.14 o'clock."
# A command row of --help: four spaces, the command name, then its summary (or a new line
# when the name is too long for the column; the summary then follows on the next line).
_HELP_ROW = re.compile(r"^    (?P<name>[^\s<]\S*)")


def _expected_commands() -> Dict[str, Callable[..., Any]]:
    """Return the commands the plan's rule defines: public, own module, one required param."""
    commands: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            params = inspect.signature(func).parameters.values()
            required = [
                p
                for p in params
                if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            if len(required) == 1:
                commands[name] = func
    return commands


def _run(*args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``python -m textkit *args`` from the repository root and capture its output.

    UTF-8 is forced for the child's stdio so non-ASCII results do not depend on the locale,
    and COLUMNS is widened so argparse does not wrap the --help summaries.
    """
    env = dict(os.environ, PYTHONIOENCODING="utf-8", COLUMNS="1000")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )


def _printed(result: Any) -> str:
    """Return what the plan says the CLI prints for ``result``, newline included."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    return f"{result}\n"


class HelpTest(unittest.TestCase):
    """``--help`` lists exactly the commands of the rule, each with its docstring summary."""

    def setUp(self) -> None:
        self.proc = _run("--help")

    def test_exits_0_on_stdout(self) -> None:
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertEqual(self.proc.stderr, "")
        self.assertIn("usage:", self.proc.stdout)

    def test_command_list_equals_the_computed_set(self) -> None:
        listed = [m["name"] for m in map(_HELP_ROW.match, self.proc.stdout.splitlines()) if m]
        self.assertEqual(sorted(listed), sorted(_expected_commands()))
        self.assertEqual(len(listed), len(set(listed)), "a command is listed twice")

    def test_each_command_shows_the_first_docstring_line(self) -> None:
        flat = " ".join(self.proc.stdout.split())
        for name, func in _expected_commands().items():
            with self.subTest(command=name):
                summary = inspect.getdoc(func).splitlines()[0]
                self.assertIn(f"{name} {' '.join(summary.split())}", flat)

    def test_the_rule_selects_and_rejects_as_expected(self) -> None:
        # Guards the rule itself against drift: one-text helpers are in, helpers with a
        # second required parameter and private helpers are out.
        commands = _expected_commands()
        for name in ("slugify", "word_count", "char_freq", "to_snake_case"):
            self.assertIn(name, commands)
        for name in ("truncate", "wrap", "words", "_main"):
            self.assertNotIn(name, commands)


class RunEveryCommandTest(unittest.TestCase):
    """Every command runs once via subprocess and prints its result in the planned format."""

    def test_every_command(self) -> None:
        commands = _expected_commands()
        self.assertTrue(commands, "no command discovered")
        for name, func in commands.items():
            with self.subTest(command=name):
                proc = _run(name, _SAMPLE)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stderr, "")
                self.assertEqual(proc.stdout, _printed(func(_SAMPLE)))


class OutputFormatTest(unittest.TestCase):
    """``_format``: str as is, bool and int via print, dict and list as sorted JSON."""

    def test_str_is_printed_as_is(self) -> None:
        self.assertEqual(_format("a  \"b\"\tÑ"), "a  \"b\"\tÑ")

    def test_bool_and_int(self) -> None:
        self.assertEqual(_format(True), "True")
        self.assertEqual(_format(False), "False")
        self.assertEqual(_format(0), "0")
        self.assertEqual(_format(42), "42")

    def test_dict_is_json_with_sorted_keys_and_non_ascii_kept(self) -> None:
        self.assertEqual(_format({"ú": 1, "a": 2}), '{"a": 2, "ú": 1}')

    def test_list_is_json(self) -> None:
        self.assertEqual(_format(["Ñ", "b"]), '["Ñ", "b"]')
        self.assertEqual(_format([]), "[]")

    def test_dict_output_through_the_cli(self) -> None:
        proc = _run("char_freq", "baú")
        self.assertEqual(proc.stdout, '{"a": 1, "b": 1, "ú": 1}\n')


class ErrorsTest(unittest.TestCase):
    """Usage errors exit 2 with the message on stderr and nothing on stdout."""

    def assertUsageError(self, *args: str) -> "subprocess.CompletedProcess[str]":
        proc = _run(*args)
        self.assertEqual(proc.returncode, 2, proc)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)
        self.assertIn("error:", proc.stderr)
        return proc

    def test_no_arguments_prints_usage_and_exits_2(self) -> None:
        self.assertUsageError()

    def test_unknown_function(self) -> None:
        self.assertIn("no_such_function", self.assertUsageError("no_such_function", "x").stderr)

    def test_function_with_two_required_parameters_is_not_a_command(self) -> None:
        self.assertUsageError("truncate", "hello")

    def test_private_helper_is_not_a_command(self) -> None:
        self.assertUsageError("words", "hello")

    def test_missing_text(self) -> None:
        self.assertUsageError("slugify")

    def test_two_texts(self) -> None:
        self.assertUsageError("slugify", "a", "b")


class MainTest(unittest.TestCase):
    """``_main`` returns the status instead of raising ``SystemExit``."""

    def call(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = _main(argv)
        return status, out.getvalue(), err.getvalue()

    def test_success_returns_0(self) -> None:
        self.assertEqual(self.call(["slugify", "Hello, World!"]), (0, "hello-world\n", ""))

    def test_usage_error_returns_2(self) -> None:
        status, out, err = self.call([])
        self.assertEqual((status, out), (2, ""))
        self.assertIn("usage:", err)

    def test_help_returns_0(self) -> None:
        status, out, _ = self.call(["--help"])
        self.assertEqual(status, 0)
        self.assertIn("usage:", out)

    def test_import_has_no_side_effects(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-c", "import textkit.__main__"],
            cwd=_ROOT,
            capture_output=True,
            encoding="utf-8",
            timeout=60,
        )
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))


class BuildParserTest(unittest.TestCase):
    """``_build_parser`` and ``_call`` on made-up commands, for cases no helper has yet."""

    def test_percent_in_a_docstring_does_not_break_help(self) -> None:
        def pct(text: str) -> str:
            """Return 100% of ``text``."""
            return text

        help_text = _build_parser({"pct": pct}).format_help()
        self.assertIn("Return 100% of ``text``.", " ".join(help_text.split()))

    def test_keyword_only_text_parameter(self) -> None:
        def kw(*, text: str, times: int = 2) -> str:
            """Repeat ``text``."""
            return text * times

        self.assertEqual(_call(kw, "ab"), "abab")


class VersionTest(unittest.TestCase):
    """``--version`` prints ``textkit <version>`` from ``textkit.__version__`` (T2.7)."""

    def test_version_option_prints_the_package_version(self) -> None:
        proc = _run("--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.stdout, f"textkit {textkit.__version__}\n")

    def test_package_version(self) -> None:
        self.assertEqual(textkit.__version__, "0.1.0")

    def test_version_is_written_only_in_init(self) -> None:
        # The plan makes __init__.py the single source; a copy elsewhere would drift.
        holders = sorted(
            p.name
            for p in (_ROOT / "textkit").glob("*.py")
            if textkit.__version__ in p.read_text(encoding="utf-8")
        )
        self.assertEqual(holders, ["__init__.py"])

    def test_main_returns_0_for_version(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = _main(["--version"])
        self.assertEqual((status, out.getvalue(), err.getvalue()), (0, "textkit 0.1.0\n", ""))


if __name__ == "__main__":
    unittest.main()
