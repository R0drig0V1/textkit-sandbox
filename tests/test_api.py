"""API contract of textkit (plan task T2.5): every public function is documented, fully
type-hinted and listed in the README function table.

Nothing is hard-coded: modules are discovered with ``pkgutil.iter_modules(textkit.__path__)``
and functions with ``inspect.getmembers(module, inspect.isfunction)``, so new modules and new
functions are checked as soon as they land. "Public function" is the definition of phase 1
(docs/phases/phase-1-core-helpers.md, "Rules for every task"): a top-level function whose
name does not start with ``_``, in a module whose name does not start with ``_``. Private
modules such as ``_tokens`` and ``__main__`` are skipped without being imported.
"""

import importlib
import inspect
import pathlib
import pkgutil
import re
import types
import typing
import unittest

import textkit

README = pathlib.Path(__file__).resolve().parents[1] / "README.md"

# A row of the README function table: | `name` | `textkit.module` | what it does |
_README_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_modules() -> list[types.ModuleType]:
    """Import and return every public module of the textkit package, in discovery order."""
    return [
        importlib.import_module(f"{textkit.__name__}.{info.name}")
        for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_")
    ]


def _public_functions() -> list[tuple[str, str, types.FunctionType]]:
    """Return ``(qualified module name, function name, function)`` for every public function.

    ``f.__module__ == module.__name__`` drops names a module merely imports (``from x import
    f``), so each function is reported once, by the module that defines it.
    """
    found = []
    for module in _public_modules():
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and func.__module__ == module.__name__:
                found.append((module.__name__, name, func))
    return found


def _readme_rows() -> list[tuple[str, str]]:
    """Return ``(function, module)`` for every row of the README function table."""
    text = README.read_text(encoding="utf-8")
    # Only the "## Functions" section holds the table; stop at the next section.
    section = text.split("## Functions", 1)[1].split("\n## ", 1)[0]
    return _README_ROW.findall(section)


class ApiContractTest(unittest.TestCase):
    """Every public function has a docstring, full type hints and one README row."""

    def setUp(self) -> None:
        self.functions = _public_functions()

    def test_discovery_finds_functions(self) -> None:
        # Guards the other tests against passing vacuously if discovery ever breaks.
        self.assertTrue(self.functions, "no public function discovered in textkit")

    def test_every_public_function_has_a_docstring(self) -> None:
        for module, name, func in self.functions:
            with self.subTest(function=f"{module}.{name}"):
                self.assertTrue((func.__doc__ or "").strip(), f"{module}.{name} has no docstring")

    def test_every_parameter_and_return_value_has_a_type_hint(self) -> None:
        for module, name, func in self.functions:
            qualname = f"{module}.{name}"
            with self.subTest(function=qualname):
                # get_type_hints evaluates the annotations, so one that does not evaluate on
                # the running Python (``X | Y`` on 3.9, an undefined name) fails here.
                try:
                    hints = typing.get_type_hints(func)
                except Exception as exc:  # noqa: BLE001 - any failure is a contract breach
                    self.fail(f"{qualname}: type hints do not evaluate: {exc!r}")
                params = inspect.signature(func).parameters
                missing = [param for param in params if param not in hints]
                if "return" not in hints:
                    missing.append("return")
                self.assertEqual(missing, [], f"{qualname} lacks type hints for {missing}")

    def test_discovered_functions_equal_the_readme_table(self) -> None:
        discovered = [(name, module) for module, name, _ in self.functions]
        # assertCountEqual also catches a function listed twice in the README.
        self.assertCountEqual(_readme_rows(), discovered)


if __name__ == "__main__":
    unittest.main()
