"""API contract test for the whole ``textkit`` package (plan task T2.5).

Every public function (the phase 1 definition: a top-level function whose name does not start
with ``_``, defined in a ``textkit`` module whose name does not start with ``_``) must have a
docstring and type hints for every parameter and its return value, and the set of public
functions must equal the README function table.

Nothing is hard-coded: modules are discovered with ``pkgutil.iter_modules`` and functions with
``inspect.getmembers``, so a new function is checked as soon as it is added. Hints are read
with ``typing.get_type_hints`` on purpose: it evaluates the annotations, so one that does not
evaluate on the running Python (``X | Y`` on 3.9, say) fails here instead of in a user's code.
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

# A README function-table row: "| `name` | `textkit.module` | ... |". scripts/check.sh reads
# the same rows by their first cell; the module cell is read here too, so a row that names
# the wrong module fails.
_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_functions() -> dict[str, typing.Callable[..., typing.Any]]:
    """Map ``"textkit.<module>.<name>"`` to each public function of the package."""
    found = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        # Private modules (_tokens, __main__) hold no public functions by definition, and
        # skipping them also avoids importing __main__.
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Functions imported from elsewhere belong to the module that defines them.
            if func.__module__ == module.__name__ and not name.startswith("_"):
                found[f"{module.__name__}.{name}"] = func
    return found


class ApiContractTest(unittest.TestCase):
    def setUp(self):
        self.functions = _public_functions()

    def test_discovers_functions(self):
        # Guards the other tests against passing vacuously if discovery breaks.
        self.assertTrue(self.functions)

    def test_every_public_function_has_a_docstring(self):
        for qualname, func in self.functions.items():
            with self.subTest(function=qualname):
                doc = inspect.getdoc(func)
                self.assertTrue(doc and doc.strip(), f"{qualname} has no docstring")

    def test_every_parameter_and_return_value_has_a_type_hint(self):
        for qualname, func in self.functions.items():
            with self.subTest(function=qualname):
                # Raises (and so fails the test) if an annotation does not evaluate.
                hints = typing.get_type_hints(func)
                params = inspect.signature(func).parameters
                missing = [p for p in params if p not in hints]
                if "return" not in hints:
                    missing.append("return")
                self.assertEqual(missing, [], f"{qualname} lacks type hints")

    def test_discovered_set_equals_readme_function_table(self):
        rows = _ROW.findall(README.read_text(encoding="utf-8"))
        table = {f"{module}.{name}" for name, module in rows}
        # A repeated row would vanish in the set; check.sh rejects it too, but say so here.
        self.assertEqual(len(rows), len(table), "README function table repeats a row")
        self.assertEqual(table, set(self.functions))


if __name__ == "__main__":
    unittest.main()
