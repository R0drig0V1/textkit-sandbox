"""Tests for textkit.__main__, the ``python3 -m textkit`` command line (plan tasks T2.6, T2.7).

Two kinds of test:

- Against the real package, through ``subprocess`` with ``sys.executable -m textkit``: the
  ``--help`` command list equals the set computed here from the phase-1 public-function
  definition, and every command runs once with a generic argument (``"1"`` for an ``int``
  parameter, ``"a"`` otherwise) without a traceback. Nothing is hard-coded per function, so
  later functions need no change to this file.
- In-process, with stub commands patched in over ``textkit.__main__._commands``: argument
  conversion, ``--``, output formats and exit codes. Argparse's exit 2 is a ``SystemExit``.
- ``--version`` (T2.7): through ``subprocess`` its output equals
  ``f"textkit {textkit.__version__}\n"``, and ``textkit.__version__`` is ``"0.1.0"``.

No test writes files under ``textkit/``.
"""

import ast
import contextlib
import importlib
import inspect
import io
import pathlib
import pkgutil
import subprocess
import sys
import typing
import unittest
from typing import Callable, Dict, List, Tuple
from unittest import mock

import textkit
import textkit.__main__ as cli

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _required_parameters(func: Callable[..., object]) -> List[inspect.Parameter]:
    """Parameters of ``func`` without a default, ``*args``/``**kwargs`` excluded."""
    return [
        p
        for p in inspect.signature(func).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]


def _public_functions() -> Dict[str, Callable[..., object]]:
    """Every public function of textkit, by the phase-1 definition, found with inspect."""
    found: Dict[str, Callable[..., object]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and func.__module__ == module.__name__:
                found[name] = func
    return found


def _expected_commands() -> Dict[str, Callable[..., object]]:
    """The public functions with exactly one parameter without a default."""
    return {n: f for n, f in _public_functions().items() if len(_required_parameters(f)) == 1}


def _run_module(*args: str) -> subprocess.CompletedProcess:
    """Run ``python -m textkit <args>`` from the repository root, capturing text output."""
    return subprocess.run(
        [sys.executable, "-m", "textkit", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _run_stub(
    argv: List[str], commands: Dict[str, Callable[..., object]], stdout: typing.TextIO = None
) -> Tuple[int, str, str]:
    """Call ``_main(argv)`` with ``commands`` in place of discovery.

    Returns ``(exit code, stdout, stderr)``; a ``SystemExit`` from argparse gives its code.
    """
    out = stdout if stdout is not None else io.StringIO()
    err = io.StringIO()
    with mock.patch.object(cli, "_commands", return_value=commands):
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli._main(argv)
            except SystemExit as exc:
                code = exc.code
    return code, (out.getvalue() if isinstance(out, io.StringIO) else ""), err.getvalue()


# Stub commands: each follows the rule (exactly one parameter without a default).
def _echo(text: str) -> str:
    """Return the text unchanged."""
    return text


def _double(n: int) -> int:
    """Return twice n."""
    return n * 2


def _with_default(text: str, suffix: str = "!") -> str:
    """Return the text followed by a suffix that keeps its default."""
    return text + suffix


def _keyword_only(*, text: str) -> str:
    """Return the text, received as a keyword-only argument."""
    return text.upper()


def _mapping(text: str) -> Dict[str, object]:
    """Return a dict with keys out of order and a non-ASCII value."""
    return {"z": 1, "a": text}


def _sequence(text: str) -> List[str]:
    """Return a list."""
    return [text, "ñ"]


def _truth(text: str) -> bool:
    """Return True."""
    return True


def _raises(exc: BaseException) -> Callable[[str], str]:
    def stub(text: str) -> str:
        """Raise the given exception."""
        raise exc

    return stub


STUBS = {
    "echo": _echo,
    "double": _double,
    "with_default": _with_default,
    "keyword_only": _keyword_only,
    "mapping": _mapping,
    "sequence": _sequence,
    "truth": _truth,
    "value_error": _raises(ValueError("bad value")),
    "key_error": _raises(KeyError("missing")),
    "type_error": _raises(TypeError("bad type")),
}


class CommandsTest(unittest.TestCase):
    """``_commands()`` discovers exactly the eligible public functions."""

    def test_discovery_matches_public_function_definition(self):
        self.assertEqual(set(cli._commands()), set(_expected_commands()))

    def test_inspect_finds_the_same_public_functions_as_check_sh(self):
        # check.sh finds public functions as top-level `def`s with ast; the definition in
        # phase 1 also skips modules whose name starts with `_` (this one included).
        by_ast = {
            node.name
            for path in (REPO_ROOT / "textkit").glob("*.py")
            if not path.name.startswith("_")
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        }
        self.assertEqual(set(_public_functions()), by_ast)

    def test_functions_with_several_required_parameters_are_left_out(self):
        public = _public_functions()
        for name, func in public.items():
            with self.subTest(name=name):
                self.assertEqual(name in cli._commands(), len(_required_parameters(func)) == 1)

    def test_main_module_contributes_no_commands(self):
        self.assertFalse(any(f.__module__ == cli.__name__ for f in cli._commands().values()))


class HelpTest(unittest.TestCase):
    """``--help`` lists every command with the first line of its docstring."""

    def test_help_lists_exactly_the_expected_commands(self):
        result = _run_module("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        listed = {}
        lines = result.stdout.splitlines()
        start = lines.index("commands:") + 1
        for line in lines[start:]:
            if not line.strip():
                break
            name, _, summary = line.strip().partition(" ")
            listed[name] = summary.strip()
        expected = _expected_commands()
        self.assertEqual(set(listed), set(expected))
        for name, func in expected.items():
            with self.subTest(name=name):
                first_line = (inspect.getdoc(func) or "").splitlines()[0].strip()
                self.assertEqual(listed[name], first_line)


class EveryCommandTest(unittest.TestCase):
    """Every discovered command runs once in a subprocess without a traceback."""

    def test_every_command_runs(self):
        for name, func in sorted(_expected_commands().items()):
            (param,) = _required_parameters(func)
            hint = typing.get_type_hints(func).get(param.name)
            arg = "1" if hint is int else "a"
            with self.subTest(command=name, argument=arg):
                result = _run_module(name, arg)
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertNotIn("Traceback", result.stderr)


class UsageErrorTest(unittest.TestCase):
    """Exit 2, with the message on stderr, for usage errors."""

    def test_no_arguments_prints_usage_and_exits_2(self):
        code, out, err = _run_stub([], STUBS)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("usage:", err)

    def test_no_arguments_in_a_subprocess(self):
        result = _run_module()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unknown_function_exits_2(self):
        code, _, err = _run_stub(["nope", "a"], STUBS)
        self.assertEqual(code, 2)
        self.assertIn("nope", err)

    def test_missing_argument_exits_2(self):
        code, _, err = _run_stub(["echo"], STUBS)
        self.assertEqual(code, 2)
        self.assertIn("required", err)

    def test_two_arguments_exit_2(self):
        code, _, err = _run_stub(["echo", "a", "b"], STUBS)
        self.assertEqual(code, 2)
        self.assertIn("unrecognized", err)

    def test_argument_starting_with_dash_needs_double_dash(self):
        code, _, _ = _run_stub(["echo", "-x"], STUBS)
        self.assertEqual(code, 2)


class ArgumentConversionTest(unittest.TestCase):
    """``int`` parameters take ``-?[0-9]+``; everything else is passed as typed."""

    def test_double_dash_before_dash_text_exits_0(self):
        self.assertEqual(_run_stub(["echo", "--", "-x"], STUBS), (0, "-x\n", ""))

    def test_int_argument_is_converted(self):
        self.assertEqual(_run_stub(["double", "21"], STUBS), (0, "42\n", ""))

    def test_negative_int_needs_no_double_dash(self):
        self.assertEqual(_run_stub(["double", "-3"], STUBS), (0, "-6\n", ""))

    def test_non_integer_for_int_parameter_exits_2(self):
        for arg in ["1a", "", " 1", "1 ", "1\n", "+1", "1.0", "0x1", "1_000", "٣", "-"]:
            with self.subTest(arg=arg):
                code, out, err = _run_stub(["double", "--", arg], STUBS)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn("not an integer", err)

    def test_int_refusing_the_digits_exits_2(self):
        # Python 3.11+ limits int() on strings (4300 digits by default); 3.9 has no limit.
        if not hasattr(sys, "set_int_max_str_digits"):
            self.skipTest("int() has no digit limit before Python 3.11")
        previous = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(4300)
        try:
            code, out, err = _run_stub(["double", "1" * 5000], STUBS)
        finally:
            sys.set_int_max_str_digits(previous)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not a usable integer", err)

    def test_str_argument_is_passed_as_typed(self):
        self.assertEqual(_run_stub(["echo", "1"], STUBS), (0, "1\n", ""))

    def test_parameters_with_defaults_keep_them(self):
        self.assertEqual(_run_stub(["with_default", "a"], STUBS), (0, "a!\n", ""))

    def test_keyword_only_parameter(self):
        self.assertEqual(_run_stub(["keyword_only", "a"], STUBS), (0, "A\n", ""))


class OutputTest(unittest.TestCase):
    """``str`` as is, ``bool``/``int`` with ``print()``, ``dict``/``list`` as sorted JSON."""

    def test_str(self):
        self.assertEqual(_run_stub(["echo", "a b"], STUBS), (0, "a b\n", ""))

    def test_bool(self):
        self.assertEqual(_run_stub(["truth", "a"], STUBS), (0, "True\n", ""))

    def test_dict_is_sorted_json_without_ascii_escapes(self):
        self.assertEqual(_run_stub(["mapping", "ñ"], STUBS), (0, '{"a": "ñ", "z": 1}\n', ""))

    def test_list_is_json(self):
        self.assertEqual(_run_stub(["sequence", "a"], STUBS), (0, '["a", "ñ"]\n', ""))


class FunctionErrorTest(unittest.TestCase):
    """``ValueError``/``KeyError``/``TypeError`` give ``error: <message>`` and exit 1."""

    def test_function_errors_exit_1(self):
        for name, message in [
            ("value_error", "bad value"),
            ("key_error", "missing"),
            ("type_error", "bad type"),
        ]:
            with self.subTest(name=name):
                code, out, err = _run_stub([name, "a"], STUBS)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("error: "), err)
                self.assertIn(message, err)
                self.assertNotIn("Traceback", err)

    def test_unencodable_output_exits_1(self):
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
        code, _, err = _run_stub(["echo", "ñ"], STUBS, stdout=stdout)
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("error: "), err)

    def test_other_exceptions_are_not_swallowed(self):
        commands = {"boom": _raises(RuntimeError("bug"))}
        with self.assertRaises(RuntimeError):
            _run_stub(["boom", "a"], commands)


class ImportTest(unittest.TestCase):
    """Importing ``textkit.__main__`` has no side effects."""

    def test_import_prints_nothing(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            importlib.reload(cli)
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))



class VersionTest(unittest.TestCase):
    """``--version`` prints ``textkit <version>`` from ``textkit.__version__`` (T2.7)."""

    def test_version_flag_prints_the_package_version(self):
        result = _run_module("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"textkit {textkit.__version__}\n")
        self.assertEqual(result.stderr, "")

    def test_package_version_is_0_1_0(self):
        self.assertEqual(textkit.__version__, "0.1.0")

    def test_version_string_appears_only_in_init(self):
        # __main__.py must read textkit.__version__, not repeat the literal.
        holders = sorted(
            path.name
            for path in (REPO_ROOT / "textkit").glob("*.py")
            if textkit.__version__ in path.read_text(encoding="utf-8")
        )
        self.assertEqual(holders, ["__init__.py"])


if __name__ == "__main__":
    unittest.main()
