"""Tests for textkit/errors.py, the error hierarchy (plan task T3.2, ADR 0006).

Four things are checked:

- the hierarchy: ``InvalidValueError`` is a ``TextkitError`` and not a ``ValueError``;
- the source: every ``*.py`` under ``textkit/``, subpackages included, is parsed with ``ast``
  and must not raise ``ValueError``, call ``ValueError(...)`` or subclass ``ValueError``
  (catching one from the standard library is allowed: phase 3 rule "Errors");
- the runtime: every module that ``pkgutil.walk_packages`` finds is imported, and every
  exception class it defines is a ``TextkitError``;
- the command line: a ``TextkitError`` from a function command exits 1 with the message on
  stderr and no traceback, and a plain ``ValueError`` propagates out of ``_main``.

Nothing is listed by hand, so a module, a subpackage or an error class added later is checked
with no change here.
"""

import ast
import importlib
import inspect
import pathlib
import pkgutil
import unittest
from typing import List
from unittest import mock

import textkit
import textkit.cli.main as cli
from tests.test_cli import _fake_module, _main_captured
from textkit.cli.registry import PROG
from textkit.errors import InvalidValueError, TextkitError

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "textkit"


def _is_value_error(node: ast.expr) -> bool:
    """Whether ``node`` names ``ValueError`` (``ValueError`` or ``<anything>.ValueError``)."""
    if isinstance(node, ast.Name):
        return node.id == "ValueError"
    return isinstance(node, ast.Attribute) and node.attr == "ValueError"


def _value_error_uses(source: str) -> List[str]:
    """Describe every forbidden use of ``ValueError`` in ``source``, one ``line N: ...`` each.

    Forbidden: ``raise ValueError`` (with or without arguments), any call ``ValueError(...)``
    (building one to raise or return later is the same thing) and a class with ``ValueError``
    among its bases. ``except ValueError`` is allowed: it is how a standard-library error is
    caught and turned into textkit's own.
    """
    tree = ast.parse(source)
    # The call in "raise ValueError(...)" is reported as the raise, not a second time.
    raised = {id(node.exc) for node in ast.walk(tree) if isinstance(node, ast.Raise)}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if _is_value_error(exc):
                found.append(f"line {node.lineno}: raise ValueError")
        elif isinstance(node, ast.Call) and _is_value_error(node.func):
            if id(node) not in raised:
                found.append(f"line {node.lineno}: call ValueError(...)")
        elif isinstance(node, ast.ClassDef) and any(map(_is_value_error, node.bases)):
            found.append(f"line {node.lineno}: class {node.name} subclasses ValueError")
    return found


class HierarchyTest(unittest.TestCase):
    def test_invalid_value_error_is_a_textkit_error(self) -> None:
        self.assertTrue(issubclass(InvalidValueError, TextkitError))
        self.assertTrue(issubclass(TextkitError, Exception))

    def test_invalid_value_error_is_not_a_value_error(self) -> None:
        self.assertFalse(issubclass(InvalidValueError, ValueError))
        self.assertFalse(issubclass(TextkitError, ValueError))
        with self.assertRaises(InvalidValueError):
            try:
                raise InvalidValueError("bad")
            except ValueError:
                self.fail("except ValueError caught an InvalidValueError")

    def test_message_is_kept(self) -> None:
        self.assertEqual(str(InvalidValueError("width must be at least 1, got 0")),
                         "width must be at least 1, got 0")


class SourceTest(unittest.TestCase):
    def test_the_checker_finds_each_forbidden_use(self) -> None:
        # Guards test_no_value_error_in_textkit against passing because the checker is blind.
        cases = {
            "raise ValueError": 1,
            "raise ValueError('x')": 1,
            "raise builtins.ValueError('x') from None": 1,
            "error = ValueError('x')": 1,
            "class E(ValueError): pass": 1,
            "class E(Exception, builtins.ValueError): pass": 1,
            "try:\n    int(s)\nexcept ValueError as exc:\n    raise E(str(exc)) from exc": 0,
            "raise InvalidValueError('ValueError')": 0,
        }
        for source, count in cases.items():
            with self.subTest(source=source):
                self.assertEqual(len(_value_error_uses(source)), count)

    def test_no_value_error_in_textkit(self) -> None:
        paths = sorted(PACKAGE.rglob("*.py"))
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(file=relative):
                uses = _value_error_uses(path.read_text(encoding="utf-8"))
                self.assertEqual(uses, [], f"{relative} uses ValueError as its own error")
        # rglob recursed: a file of a subpackage was parsed, not only the top level.
        self.assertIn(PACKAGE / "cli" / "main.py", paths)
        self.assertTrue(any(path.parent == PACKAGE / "cli" for path in paths))


class RuntimeTest(unittest.TestCase):
    def test_every_exception_class_is_a_textkit_error(self) -> None:
        imported = []
        for info in pkgutil.walk_packages(textkit.__path__, f"{textkit.__name__}."):
            module = importlib.import_module(info.name)
            imported.append(module.__name__)
            for name, value in inspect.getmembers(module, inspect.isclass):
                # Only the classes the module defines: imported ones are checked where they
                # are defined.
                if value.__module__ != module.__name__ or not issubclass(value, BaseException):
                    continue
                with self.subTest(error=f"{module.__name__}.{name}"):
                    self.assertTrue(issubclass(value, TextkitError))
        # walk_packages recursed into textkit/cli/, and found the hierarchy itself.
        self.assertIn("textkit.cli.registry", imported)
        self.assertIn("textkit.errors", imported)


class CommandLineTest(unittest.TestCase):
    """``_main`` on fake function commands (as in ``tests/test_cli.py``)."""

    def setUp(self) -> None:
        fake = _fake_module(
            "textkit.fake",
            "from textkit.errors import InvalidValueError\n"
            "class ToolError(InvalidValueError): pass\n"
            "def rejects(text): raise InvalidValueError(f'bad text: {text}')\n"
            "def tool_error(text): raise ToolError('from a tool package')\n"
            "def bug(text): return int(text)\n",
        )
        patcher = mock.patch.object(cli, "_textkit_modules", return_value=[fake])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_invalid_value_error_exits_1_with_the_message(self) -> None:
        self.assertEqual(
            _main_captured(["rejects", "x"]),
            (1, "", f"{PROG} rejects: error: bad text: x\n"),
        )

    def test_a_subclass_of_textkit_error_exits_1(self) -> None:
        self.assertEqual(
            _main_captured(["tool_error", "x"]),
            (1, "", f"{PROG} tool_error: error: from a tool package\n"),
        )

    def test_plain_value_error_propagates(self) -> None:
        # int("x") raises the standard library's ValueError: a bug, so it is not caught.
        with self.assertRaises(ValueError) as caught:
            _main_captured(["bug", "x"])
        self.assertNotIsInstance(caught.exception, TextkitError)


if __name__ == "__main__":
    unittest.main()
