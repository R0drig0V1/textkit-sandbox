"""Tests for ``textkit/errors.py``, the error hierarchy (plan task T3.2, ADR 0006).

Three layers keep textkit free of ``ValueError`` as its own error:

- the hierarchy itself (``InvalidValueError`` is a ``TextkitError`` and not a ``ValueError``);
- a source scan: every ``*.py`` under ``textkit/``, subpackages included, is parsed with
  ``ast`` and may not raise or build a ``ValueError`` or subclass it. This is what fails when
  a phase 3 task merges code written before T3.2 (phase 3 rule "Errors": whichever merges
  second converts);
- a runtime scan: every module ``pkgutil.walk_packages`` yields is imported, and every
  exception class it defines must be a ``TextkitError`` (and not a ``ValueError``). This
  catches classes the source scan cannot see, such as one built by a factory.

Then the command line: ``_main`` turns a ``TextkitError`` from a function command into exit 1
and a message, and lets a plain ``ValueError`` (a bug) propagate.
"""

import ast
import importlib
import inspect
import pathlib
import pkgutil
import unittest
from typing import List, Tuple
from unittest import mock

import textkit
import textkit.cli.main as cli
from textkit.errors import InvalidValueError, TextkitError
from tests.test_cli import _fake_module, _main_captured

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "textkit"


def _is_value_error(node: ast.AST) -> bool:
    """Whether ``node`` names the built-in ``ValueError`` (``ValueError`` or ``x.ValueError``).

    The match is on the whole name, so ``InvalidValueError`` is not one.
    """
    if isinstance(node, ast.Name):
        return node.id == "ValueError"
    if isinstance(node, ast.Attribute):
        return node.attr == "ValueError"
    return False


def _value_error_uses(source: str) -> List[Tuple[int, str]]:
    """Return ``(line, what)`` for every banned use of ``ValueError`` in ``source``.

    Banned: ``raise ValueError`` (with or without a call), any call ``ValueError(...)``
    (building one to raise later counts too) and a class with ``ValueError`` among its bases.
    Catching one (``except ValueError``) is allowed: that is how textkit turns a
    standard-library ``ValueError`` into its own error (phase 3 rule "Errors").
    """
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if _is_value_error(exc):
                found.append((node.lineno, "raise ValueError"))
        elif isinstance(node, ast.Call) and _is_value_error(node.func):
            found.append((node.lineno, "call ValueError(...)"))
        elif isinstance(node, ast.ClassDef) and any(_is_value_error(b) for b in node.bases):
            found.append((node.lineno, f"class {node.name} subclasses ValueError"))
    # A "raise ValueError(...)" is both a Raise and a Call: report the line once per kind.
    return sorted(set(found))


class HierarchyTest(unittest.TestCase):
    def test_invalid_value_error_is_a_textkit_error(self) -> None:
        self.assertTrue(issubclass(TextkitError, Exception))
        self.assertTrue(issubclass(InvalidValueError, TextkitError))

    def test_invalid_value_error_is_not_a_value_error(self) -> None:
        self.assertFalse(issubclass(InvalidValueError, ValueError))
        self.assertFalse(issubclass(TextkitError, ValueError))
        with self.assertRaises(InvalidValueError):
            try:
                raise InvalidValueError("x")
            except ValueError:  # must not catch it
                self.fail("InvalidValueError was caught as a ValueError")

    def test_message_is_kept(self) -> None:
        self.assertEqual(str(InvalidValueError("width must be at least 1, got 0")),
                         "width must be at least 1, got 0")


class SourceScanTest(unittest.TestCase):
    """No ``ValueError`` raised, built or subclassed anywhere under ``textkit/``."""

    def test_the_scanner_finds_every_banned_form(self) -> None:
        # Guards the scan below against passing vacuously if _value_error_uses breaks.
        cases = {
            "raise ValueError('x')": ["raise ValueError"],
            "raise ValueError": ["raise ValueError"],
            "raise builtins.ValueError('x')": ["raise ValueError"],
            "e = ValueError('x')": ["call ValueError(...)"],
            "class E(ValueError): pass": ["class E subclasses ValueError"],
            "class E(TextkitError, ValueError): pass": ["class E subclasses ValueError"],
            "def f():\n    if x:\n        raise ValueError('nested')": ["raise ValueError"],
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                kinds = {what for _, what in _value_error_uses(source)}
                self.assertTrue(set(expected) <= kinds, kinds)

    def test_the_scanner_allows_the_rest(self) -> None:
        for source in (
            "raise InvalidValueError('x')",
            "class E(InvalidValueError): pass",
            "try:\n    int(s)\nexcept ValueError as exc:\n    raise InvalidValueError(s) from exc",
            "# raise ValueError in a comment",
            "s = 'raise ValueError'",
        ):
            with self.subTest(source=source):
                self.assertEqual(_value_error_uses(source), [])

    def test_no_value_error_in_textkit(self) -> None:
        paths = sorted(PACKAGE.rglob("*.py"))
        self.assertTrue(paths)
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(file=relative):
                uses = _value_error_uses(path.read_text(encoding="utf-8"))
                self.assertEqual(uses, [], f"{relative}: use InvalidValueError (ADR 0006)")
        # The scan is recursive: at least one file of a subpackage (textkit/cli/) was read.
        self.assertTrue(any(path.parent == PACKAGE / "cli" for path in paths))


class RuntimeScanTest(unittest.TestCase):
    """Every exception class a textkit module defines is a ``TextkitError``."""

    def test_every_exception_class_is_a_textkit_error(self) -> None:
        def onerror(name: str) -> None:
            # walk_packages ignores a subpackage that fails to import unless told otherwise;
            # a broken module must fail here, not shrink the scan.
            raise ImportError(f"cannot import {name}")

        names = [
            info.name
            for info in pkgutil.walk_packages(textkit.__path__, "textkit.", onerror=onerror)
        ]
        for name in names:
            # Importing __main__ is safe: it only runs the command line under
            # if __name__ == "__main__".
            module = importlib.import_module(name)
            for attr, value in inspect.getmembers(module, inspect.isclass):
                if not issubclass(value, BaseException) or value.__module__ != name:
                    continue
                with self.subTest(exception=f"{name}.{attr}"):
                    self.assertTrue(issubclass(value, TextkitError))
                    self.assertFalse(issubclass(value, ValueError))
        # The walk is recursive: it reached a module inside a subpackage.
        self.assertIn("textkit.cli.registry", names)
        self.assertIn("textkit.errors", names)


class CommandLineTest(unittest.TestCase):
    """``_main`` catches ``TextkitError`` from a function command, and nothing else."""

    def setUp(self) -> None:
        fake = _fake_module(
            "textkit.fake",
            "from textkit.errors import InvalidValueError\n"
            "def rejects(text): raise InvalidValueError('width must be at least 1, got 0')\n"
            "def buggy(text): return int(text)\n",
        )
        patcher = mock.patch.object(cli, "_textkit_modules", return_value=[fake])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_invalid_value_error_exits_1_with_the_message(self) -> None:
        code, out, err = _main_captured(["rejects", "x"])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(
            err, "python3 -m textkit rejects: error: width must be at least 1, got 0\n"
        )
        self.assertNotIn("Traceback", err)

    def test_plain_value_error_propagates(self) -> None:
        # int("x") raises the standard library's ValueError: a bug, not a rejected input.
        with self.assertRaises(ValueError):
            _main_captured(["buggy", "x"])


if __name__ == "__main__":
    unittest.main()
