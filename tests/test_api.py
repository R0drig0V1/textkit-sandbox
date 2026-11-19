"""API contract test (plan task T2.5): every public function is documented and fully typed.

Nothing here is a hard-coded list. Modules are discovered with
``pkgutil.iter_modules(textkit.__path__)`` and functions with
``inspect.getmembers(module, inspect.isfunction)``, kept only when ``f.__module__`` is the
module itself (so ``from textkit._tokens import words`` re-exports are not counted twice).
"Public" is the phase 1 definition (docs/phases/phase-1-core-helpers.md, "Rules for every
task"): a top-level function whose name does not start with ``_``, in a module whose name does
not start with ``_``. So ``_tokens.py`` and ``__main__.py`` hold no public functions, and a
new module or function is checked as soon as it exists.

For each public function the test requires a non-empty docstring and a type hint for every
parameter and for the return value. Hints are read with ``typing.get_type_hints``, which
evaluates them: an annotation that does not evaluate on the running Python (``str | None`` on
3.9) fails here instead of at a caller's first ``get_type_hints``. Finally the discovered set
must equal the README function table, module column included.
"""

import importlib
import inspect
import pathlib
import pkgutil
import re
import types
import typing
import unittest
from typing import Callable

import textkit

_README = pathlib.Path(__file__).resolve().parents[1] / "README.md"
# A row of the README function table: | `name` | `textkit.module` | what it does |
_ROW = re.compile(r"^\| `(?P<name>\w+)` \| `(?P<module>[\w.]+)` \|", re.M)


def _public_modules() -> list[types.ModuleType]:
    """Import and return every public module of ``textkit``, sorted by name."""
    names = sorted(info.name for info in pkgutil.iter_modules(textkit.__path__))
    return [importlib.import_module(f"textkit.{n}") for n in names if not n.startswith("_")]


def _public_functions() -> dict[str, Callable[..., object]]:
    """Return every public function of ``textkit`` keyed by ``"textkit.<module>.<name>"``."""
    found = {}
    for module in _public_modules():
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ == module.__name__ and not name.startswith("_"):
                found[f"{module.__name__}.{name}"] = func
    return found


def _contract_problems(func: Callable[..., object]) -> list[str]:
    """Return what ``func`` lacks under the API contract; empty when it complies."""
    problems = []
    if not (func.__doc__ or "").strip():
        problems.append("no docstring")
    try:
        hints = typing.get_type_hints(func)
    except Exception as exc:  # NameError, TypeError...: any failure to evaluate is a defect
        return problems + [f"type hints do not evaluate: {type(exc).__name__}: {exc}"]
    missing = [p for p in inspect.signature(func).parameters if p not in hints]
    if missing:
        problems.append(f"parameters without a type hint: {missing}")
    if "return" not in hints:
        problems.append("no return type hint")
    return problems


class ApiContractTest(unittest.TestCase):
    """The public API of ``textkit`` keeps its documentation and typing contract."""

    def setUp(self) -> None:
        self.functions = _public_functions()

    def test_discovery_finds_functions(self) -> None:
        # Guards against a vacuous pass: a broken discovery would make every check below
        # succeed over an empty set.
        self.assertTrue(self.functions, "no public functions discovered in textkit")

    def test_every_public_function_has_docstring_and_hints(self) -> None:
        for qualname, func in sorted(self.functions.items()):
            with self.subTest(function=qualname):
                self.assertEqual(_contract_problems(func), [])

    def test_discovered_set_equals_readme_table(self) -> None:
        rows = [f"{m['module']}.{m['name']}" for m in _ROW.finditer(_README.read_text())]
        # A list, not a set, on the README side, so a duplicated row also fails.
        self.assertEqual(sorted(rows), sorted(self.functions))


class ContractProblemsTest(unittest.TestCase):
    """The checker itself rejects what it must, so a green run means something."""

    def test_compliant_function_passes(self) -> None:
        def good(text: str, width: int = 1) -> str:
            """Documented and typed."""
            return text

        self.assertEqual(_contract_problems(good), [])

    def test_each_defect_is_reported(self) -> None:
        def no_doc(text: str) -> str:
            return text

        def no_param_hint(text, width: int) -> str:  # type: ignore[no-untyped-def]
            """Documented."""
            return text

        def no_return_hint(text: str):  # type: ignore[no-untyped-def]
            """Documented."""
            return text

        def bad_hint(text: "NoSuchType") -> str:  # type: ignore[name-defined]  # noqa: F821
            """Documented."""
            return text

        self.assertEqual(_contract_problems(no_doc), ["no docstring"])
        self.assertEqual(
            _contract_problems(no_param_hint), ["parameters without a type hint: ['text']"]
        )
        self.assertEqual(_contract_problems(no_return_hint), ["no return type hint"])
        self.assertEqual(len(_contract_problems(bad_hint)), 1)
        self.assertIn("do not evaluate", _contract_problems(bad_hint)[0])


if __name__ == "__main__":
    unittest.main()
