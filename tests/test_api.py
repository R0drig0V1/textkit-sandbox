"""API contract test (plan task T2.5): every public function is documented, typed and listed.

Nothing here is hard-coded: modules are discovered with ``pkgutil.iter_modules`` and functions
with ``inspect.getmembers``, so functions and modules added later are covered without editing
this file. "Public function" follows the phase 1 definition (docs/phases/phase-1-core-helpers.md,
"Rules for every task"): a top-level ``def`` whose name does not start with ``_``, in a module
of ``textkit/`` whose name does not start with ``_``. Private modules (``_tokens``,
``__main__``) are therefore never imported here.

Hints are read with ``typing.get_type_hints`` rather than ``__annotations__`` on purpose: it
evaluates every annotation, so one that does not evaluate on the running Python (``int | None``
on 3.9, a misspelt name in a string annotation) fails the contract instead of passing silently.
"""

import importlib
import inspect
import pathlib
import pkgutil
import re
import typing
import unittest
from types import FunctionType, ModuleType

import textkit

README = pathlib.Path(__file__).resolve().parents[1] / "README.md"

# A row of the README function table: | `name` | `textkit.module` | what it does |
README_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_modules() -> list[ModuleType]:
    """Import and return every public module of the ``textkit`` package."""
    return [
        importlib.import_module(f"{textkit.__name__}.{info.name}")
        for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_")
    ]


def _public_functions() -> list[FunctionType]:
    """Return every public function of every public ``textkit`` module.

    The ``__module__`` filter drops functions a module merely imports from elsewhere, so each
    function is reported once, under the module that defines it.
    """
    return [
        f
        for m in _public_modules()
        for name, f in inspect.getmembers(m, inspect.isfunction)
        if not name.startswith("_") and f.__module__ == m.__name__
    ]


def _contract_violations(f: typing.Callable[..., object]) -> list[str]:
    """Return what ``f`` lacks to meet the API contract; empty when it complies.

    The contract: a non-empty docstring, and a type hint that evaluates on the running Python
    for every parameter (``*args`` and ``**kwargs`` included) and for the return value.
    """
    problems = []
    if not (inspect.getdoc(f) or "").strip():
        problems.append("no docstring")
    try:
        hints = typing.get_type_hints(f)
    except Exception as exc:  # NameError, TypeError, SyntaxError...: any is a failure.
        return problems + [f"type hints do not evaluate: {type(exc).__name__}: {exc}"]
    missing = [p for p in inspect.signature(f).parameters if p not in hints]
    if missing:
        problems.append(f"parameters without a type hint: {missing}")
    if "return" not in hints:
        problems.append("no return type hint")
    return problems


class ApiContractTest(unittest.TestCase):
    """Every public function has a docstring and type hints, and the README lists exactly them."""

    def test_discovery_finds_functions(self) -> None:
        # Guards the other tests against passing vacuously if discovery ever breaks.
        self.assertTrue(_public_modules())
        self.assertTrue(_public_functions())

    def test_every_public_function_meets_the_contract(self) -> None:
        for f in _public_functions():
            with self.subTest(function=f"{f.__module__}.{f.__name__}"):
                self.assertEqual(_contract_violations(f), [])

    def test_readme_table_equals_the_public_functions(self) -> None:
        # Sorted lists, not sets, so a function listed twice in the README also fails.
        discovered = sorted(f"{f.__module__}.{f.__name__}" for f in _public_functions())
        listed = sorted(
            f"{module}.{name}" for name, module in README_ROW.findall(README.read_text())
        )
        self.assertEqual(listed, discovered)


def _ok(text: str, width: int = 1) -> str:
    """Comply with the contract."""
    return text


def _no_docstring(text: str) -> str:
    return text


def _missing_param_hint(text: str, width) -> str:
    """Leave ``width`` untyped."""
    return text


def _missing_return_hint(text: str):
    """Leave the return value untyped."""
    return text


def _untyped_varargs(*args, **kwargs: str) -> None:
    """Leave ``*args`` untyped."""


def _unevaluable_hint(text: "NoSuchType") -> str:
    """Use an annotation that does not evaluate."""
    return text


class ContractViolationsTest(unittest.TestCase):
    """The checker itself flags each kind of violation, so a green contract test means something."""

    def test_compliant_function_has_no_violations(self) -> None:
        self.assertEqual(_contract_violations(_ok), [])

    def test_each_violation_is_reported(self) -> None:
        cases = [
            (_no_docstring, "no docstring"),
            (_missing_param_hint, "['width']"),
            (_missing_return_hint, "no return type hint"),
            (_untyped_varargs, "['args']"),
            (_unevaluable_hint, "do not evaluate: NameError"),
        ]
        for f, expected in cases:
            with self.subTest(function=f.__name__):
                violations = _contract_violations(f)
                self.assertEqual(len(violations), 1, violations)
                self.assertIn(expected, violations[0])


if __name__ == "__main__":
    unittest.main()
