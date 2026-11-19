"""API contract test (plan task T2.5): every public function is documented, fully typed and
listed in the README function table.

Nothing is hard-coded: modules are discovered with ``pkgutil.iter_modules(textkit.__path__)``
and functions with ``inspect.getmembers``, applying the public-function definition of phase 1
("Rules for every task" in docs/phases/phase-1-core-helpers.md): a top-level ``def`` whose name
does not start with ``_``, in a module of ``textkit/`` whose name does not start with ``_``.
A new function or module is therefore covered as soon as it exists.
"""

import importlib
import inspect
import pathlib
import pkgutil
import re
import typing
import unittest

import textkit

README = pathlib.Path(__file__).resolve().parents[1] / "README.md"
# Same row pattern as scripts/check.sh, so both read the README table the same way.
_README_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_functions() -> dict:
    """Return ``{name: function}`` for every public function of every public module."""
    found = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Skip names imported from elsewhere (``from x import f``): only functions
            # defined in this module belong to its API.
            if func.__module__ == module.__name__ and not name.startswith("_"):
                found[name] = func
    return found


class ApiContractTest(unittest.TestCase):
    maxDiff = None  # show the whole name -> module mapping when the README table drifts

    def setUp(self):
        self.functions = _public_functions()

    def test_discovers_public_functions(self):
        # Guards against a discovery bug that finds nothing and makes the checks below vacuous.
        self.assertTrue(self.functions, "no public functions discovered in textkit")

    def test_every_public_function_has_a_docstring(self):
        for name, func in self.functions.items():
            with self.subTest(function=f"{func.__module__}.{name}"):
                doc = inspect.getdoc(func)
                self.assertTrue(doc and doc.strip(), "missing or empty docstring")

    def test_every_public_function_is_fully_typed(self):
        for name, func in self.functions.items():
            with self.subTest(function=f"{func.__module__}.{name}"):
                # get_type_hints evaluates the annotations, so one that does not evaluate on
                # the running Python (``int | None`` on 3.9) fails here, not only at call time.
                try:
                    hints = typing.get_type_hints(func)
                except Exception as exc:  # NameError, TypeError, ... from a bad annotation
                    self.fail(f"annotations do not evaluate: {exc!r}")
                params = inspect.signature(func).parameters
                missing = [p for p in params if p not in hints]
                self.assertEqual(missing, [], "parameters without a type hint")
                self.assertIn("return", hints, "no return type hint")

    def test_readme_table_lists_exactly_the_public_functions(self):
        rows = dict((name, module) for name, module in _README_ROW.findall(README.read_text()))
        self.assertEqual(set(rows), set(self.functions))
        # Each row also names the module that actually defines the function.
        self.assertEqual(rows, {n: f.__module__ for n, f in self.functions.items()})


if __name__ == "__main__":
    unittest.main()
