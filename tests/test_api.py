"""API contract test for the whole textkit package (plan task T2.5).

Every public function must have a docstring and type hints for each parameter and for its
return value, and the set of public functions must equal the README function table. Nothing
is hard-coded: modules and functions are discovered at run time, so new modules and
functions are covered as soon as they land.

"Public function" follows the definition in docs/phases/phase-1-core-helpers.md ("Rules for
every task"): a top-level function whose name does not start with `_`, in a module of
`textkit/` whose name does not start with `_`. So `textkit/_tokens.py` and
`textkit/__main__.py` contribute nothing, and helpers like `_split_camel` are skipped.
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
_README_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_modules() -> list[ModuleType]:
    """Import and return every public module of `textkit`, sorted by name."""
    return [
        importlib.import_module(f"{textkit.__name__}.{info.name}")
        for info in sorted(pkgutil.iter_modules(textkit.__path__), key=lambda i: i.name)
        if not info.name.startswith("_")
    ]


def _public_functions() -> list[tuple[str, FunctionType]]:
    """Return `(module name, function)` for every public function of `textkit`.

    The `f.__module__ == m.__name__` filter drops functions a module merely imports (for
    example `strip_accents` imported into another module), so each function is counted once,
    in the module that defines it.
    """
    return [
        (module.__name__, func)
        for module in _public_modules()
        for name, func in inspect.getmembers(module, inspect.isfunction)
        if func.__module__ == module.__name__ and not name.startswith("_")
    ]


class ApiContractTest(unittest.TestCase):
    """The contract every public function of `textkit` must meet."""

    def test_discovery_finds_functions(self) -> None:
        # Guards the other tests: an empty discovery would make them pass vacuously.
        self.assertTrue(_public_functions())

    def test_every_public_function_has_a_docstring(self) -> None:
        for module_name, func in _public_functions():
            with self.subTest(function=f"{module_name}.{func.__name__}"):
                doc = inspect.getdoc(func)
                self.assertTrue(doc and doc.strip(), "missing or empty docstring")

    def test_every_public_function_is_fully_type_hinted(self) -> None:
        for module_name, func in _public_functions():
            with self.subTest(function=f"{module_name}.{func.__name__}"):
                # get_type_hints evaluates every annotation, so one that does not evaluate
                # on the running Python (`X | Y` on 3.9, a forward reference to a missing
                # name) raises here and fails the test.
                hints = typing.get_type_hints(func)
                params = inspect.signature(func).parameters
                missing = [name for name in params if name not in hints]
                self.assertEqual(missing, [], "parameters without a type hint")
                self.assertIn("return", hints, "no return type hint")

    def test_public_functions_equal_readme_table(self) -> None:
        discovered = sorted((func.__name__, module) for module, func in _public_functions())
        rows = sorted(_README_ROW.findall(README.read_text(encoding="utf-8")))
        # Lists, not sets: a row listed twice (a merge=union artefact) also fails.
        self.assertEqual(discovered, rows)


if __name__ == "__main__":
    unittest.main()
