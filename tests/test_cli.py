"""Tests for textkit/__main__.py, the ``python3 -m textkit`` command line (plan tasks T2.6 and
T2.7: ``--version``).

Nothing here names a textkit function: the expected commands are computed from the source
files with ``ast``, independently of the ``inspect``-based discovery in ``__main__``, so a
function added to any public module is covered with no change to this file, and a gap
between the two readings of the public-function definition fails the acceptance test.
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
import unittest.mock
from typing import Any, Callable, Dict, List, Tuple

import textkit
from textkit.__main__ import _format, _main

ROOT = pathlib.Path(__file__).resolve().parents[1]
# An ordinary sentence every command should accept; it mixes punctuation, a hyphen, an
# accent and capitals so most functions have something to do.
SAMPLE = "Hello, World! Ñandú well-known HTTPServer user_id"


def _expected_commands() -> Dict[str, Callable[..., Any]]:
    """Compute the commands from the phase 1 definition of a public function, with ``ast``.

    A public function is a top-level ``def`` whose name does not start with ``_``, in a
    module of ``textkit/`` whose name does not start with ``_``; it is a command when exactly
    one of its parameters (``*args``/``**kwargs`` aside) has no default.
    """
    found: Dict[str, Callable[..., Any]] = {}
    for path in sorted((ROOT / "textkit").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            a = node.args
            positional = a.posonlyargs + a.args
            required = len(positional) - len(a.defaults)
            required += sum(1 for d in a.kw_defaults if d is None)
            if required == 1:
                module = importlib.import_module(f"textkit.{path.stem}")
                found[node.name] = getattr(module, node.name)
    return found


def _help_commands(help_text: str) -> List[str]:
    """Return the command names listed in the "functions:" section of ``--help``.

    argparse prints one sub-command per line, indented by four spaces; a summary that does
    not fit next to a long name goes on the next line, indented further, and is skipped.
    """
    lines = help_text.split("functions:\n", 1)[1].splitlines()
    names = []
    for line in lines:
        if not line.strip():
            break
        if line.startswith("    ") and not line.startswith("     "):
            names.append(line.split()[0])
    return names


def _run_main(argv: List[str]) -> Tuple[int, str, str]:
    """Run ``_main(argv)`` in process and return (status, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = _main(argv)
    return status, out.getvalue(), err.getvalue()


def _run_cli(*args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``sys.executable -m textkit *args`` from the repository root."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class CommandLineTest(unittest.TestCase):
    """Acceptance tests of T2.6, through a real ``python3 -m textkit`` process."""

    def test_help_lists_exactly_the_discovered_commands(self):
        result = _run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        listed = _help_commands(result.stdout)
        self.assertEqual(len(listed), len(set(listed)), listed)
        self.assertEqual(set(listed), set(_expected_commands()))

    def test_help_shows_the_first_docstring_line_of_every_command(self):
        result = _run_cli("--help")
        for name, func in _expected_commands().items():
            with self.subTest(command=name):
                doc = inspect.getdoc(func) or ""
                first_line = doc.splitlines()[0] if doc else ""
                self.assertIn(first_line, result.stdout)

    def test_every_command_runs_once(self):
        commands = _expected_commands()
        self.assertTrue(commands, "no commands discovered")
        for name, func in commands.items():
            with self.subTest(command=name):
                result = _run_cli(name, SAMPLE)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, _format(func(SAMPLE)) + "\n")
                self.assertEqual(result.stderr, "")

    def test_no_arguments_prints_usage_to_stderr_and_exits_2(self):
        result = _run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("usage:", result.stderr)


class MainTest(unittest.TestCase):
    """``_main`` in process: exit statuses, output formats and error messages."""

    def test_unknown_function_exits_2_with_message_on_stderr(self):
        status, out, err = _run_main(["no_such_function", "x"])
        self.assertEqual(status, 2)
        self.assertEqual(out, "")
        self.assertIn("no_such_function", err)

    def test_private_helpers_are_not_commands(self):
        status, _, err = _run_main(["_words", "x"])
        self.assertEqual(status, 2)
        self.assertIn("invalid choice", err)

    def test_too_many_arguments_exit_2(self):
        name = sorted(_expected_commands())[0]
        status, out, err = _run_main([name, "one", "two"])
        self.assertEqual(status, 2)
        self.assertEqual(out, "")
        self.assertIn("unrecognized arguments", err)

    def test_missing_text_exits_2(self):
        name = sorted(_expected_commands())[0]
        status, out, err = _run_main([name])
        self.assertEqual(status, 2)
        self.assertEqual(out, "")
        self.assertIn("text", err)

    def test_no_arguments_exit_2_with_usage(self):
        status, out, err = _run_main([])
        self.assertEqual(status, 2)
        self.assertEqual(out, "")
        self.assertIn("usage:", err)

    def test_help_exits_0(self):
        status, out, _ = _run_main(["--help"])
        self.assertEqual(status, 0)
        self.assertIn("functions:", out)

    def test_output_matches_the_result_of_each_command(self):
        for name, func in _expected_commands().items():
            with self.subTest(command=name):
                status, out, _ = _run_main([name, SAMPLE])
                self.assertEqual(status, 0)
                self.assertEqual(out, _format(func(SAMPLE)) + "\n")

    def test_value_error_exits_1_with_message_on_stderr(self):
        def reject(text: str) -> str:
            raise ValueError("bad text")

        with unittest.mock.patch("textkit.__main__._commands", return_value={"reject": reject}):
            status, out, err = _run_main(["reject", "x"])
        self.assertEqual(status, 1)
        self.assertEqual(out, "")
        self.assertIn("bad text", err)

    def test_parameters_with_defaults_keep_them(self):
        def scaled(text: str, factor: int = 3) -> int:
            return len(text) * factor

        with unittest.mock.patch("textkit.__main__._commands", return_value={"scaled": scaled}):
            status, out, _ = _run_main(["scaled", "ab"])
        self.assertEqual((status, out), (0, "6\n"))

    def test_format_str_is_printed_as_is(self):
        self.assertEqual(_format("Ñandú  x"), "Ñandú  x")

    def test_format_bool_and_int_as_print_shows_them(self):
        self.assertEqual(_format(True), "True")
        self.assertEqual(_format(0), "0")

    def test_format_dict_and_list_as_sorted_json_keeping_non_ascii(self):
        self.assertEqual(_format({"ú": 1, "a": 2}), '{"a": 2, "ú": 1}')
        self.assertEqual(_format(["ñ", "b"]), '["ñ", "b"]')
        self.assertEqual(json.loads(_format({"b": [1], "a": {}})), {"a": {}, "b": [1]})

    def test_importing_the_module_has_no_side_effects(self):
        code = "import textkit.__main__"
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


class VersionTest(unittest.TestCase):
    """Acceptance tests of T2.7: ``python3 -m textkit --version`` and ``__version__``."""

    def test_version_prints_name_and_version_and_exits_0(self):
        result = _run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"textkit {textkit.__version__}\n")
        self.assertEqual(result.stderr, "")

    def test_version_is_0_1_0(self):
        self.assertEqual(textkit.__version__, "0.1.0")

    def test_version_string_appears_only_in_init(self):
        # The plan makes __init__.py the single source of the version inside textkit/.
        holders = [
            path.relative_to(ROOT).as_posix()
            for path in sorted((ROOT / "textkit").rglob("*.py"))
            if textkit.__version__ in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(holders, ["textkit/__init__.py"])


if __name__ == "__main__":
    unittest.main()
