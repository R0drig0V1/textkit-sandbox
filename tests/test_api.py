"""API contract test (plan task T2.5): every public function is documented and fully typed.

Nothing is hard-coded: modules are discovered with ``pkgutil.iter_modules`` and functions with
``inspect.getmembers``, so functions added later are checked without touching this file.
"Public function" follows the definition in docs/phases/phase-1-core-helpers.md ("Rules for
every task"): a top-level ``def`` whose name does not start with ``_``, in a module of
``textkit/`` whose name does not start with ``_``. Private modules (``_tokens``) and
``__main__`` are therefore skipped, and never imported here, so the command line never runs.
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

README = pathlib.Path(__file__).resolve().parent.parent / "README.md"

# A row of the README function table: | `name` | `textkit.module` | what it does |
README_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.MULTILINE)


def _public_modules() -> list[ModuleType]:
    """Import and return every public module of the package, sorted by name.

    Names starting with ``_`` are filtered out *before* importing, so ``textkit.__main__``
    and private helpers such as ``textkit._tokens`` are never imported by this test.
    """
    names = sorted(
        info.name for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_")
    )
    return [importlib.import_module(f"{textkit.__name__}.{name}") for name in names]


def _public_functions() -> dict[str, FunctionType]:
    """Map ``"<module>.<name>"`` to every public function defined in a public module.

    ``f.__module__ == m.__name__`` drops names a module merely imports (from another textkit
    module or the standard library), so each function is counted once, where it is defined.
    """
    found = {}
    for module in _public_modules():
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ == module.__name__ and not name.startswith("_"):
                found[f"{module.__name__}.{name}"] = func
    return found


class ApiContractTest(unittest.TestCase):
    """The public API: docstrings, type hints, and the README function table."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.functions = _public_functions()

    def test_discovers_functions(self) -> None:
        # Guards against discovery silently finding nothing (and every loop below passing).
        self.assertTrue(self.functions, "no public functions discovered in textkit")

    def test_every_public_function_has_a_docstring(self) -> None:
        for qualname, func in self.functions.items():
            with self.subTest(function=qualname):
                self.assertTrue(
                    (func.__doc__ or "").strip(), f"{qualname} has no docstring"
                )

    def test_every_public_function_is_fully_typed(self) -> None:
        for qualname, func in self.functions.items():
            with self.subTest(function=qualname):
                # get_type_hints evaluates the annotations, so one that does not work on the
                # running Python (say `str | None` on 3.9) fails here instead of at import.
                try:
                    hints = typing.get_type_hints(func)
                except Exception as exc:  # noqa: BLE001 - any failure is a contract breach
                    self.fail(f"{qualname}: annotations do not evaluate: {exc!r}")
                params = inspect.signature(func).parameters
                missing = [p for p in params if p not in hints]
                if "return" not in hints:
                    missing.append("return")
                self.assertEqual(missing, [], f"{qualname} lacks type hints for {missing}")

    def test_discovered_functions_equal_the_readme_table(self) -> None:
        # Compared as sorted lists of (module, name), so a row in the wrong module, a duplicate
        # row, a missing row and a row for a function that does not exist all fail.
        rows = sorted(
            f"{module}.{name}" for name, module in README_ROW.findall(README.read_text())
        )
        self.assertEqual(rows, sorted(self.functions))


if __name__ == "__main__":
    unittest.main()
