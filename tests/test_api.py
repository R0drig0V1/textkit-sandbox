"""API contract test for textkit (plan task T2.5).

Every public function of every textkit module must have a docstring and type hints for all
its parameters and its return value, and the set of public functions must equal the README
function table. Nothing is hard-coded: modules and functions are discovered at run time, so
a function added by any later PR is checked without touching this file.

"Public function" is the definition of phase 1 ("Rules for every task"): a top-level ``def``
whose name does not start with ``_``, in a module of ``textkit/`` whose name does not start
with ``_``. Private modules (``_tokens``, ``__main__``) are never imported here: importing
``__main__`` would be harmless by contract (T2.6), but skipping by name keeps the test
independent of that.
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
# Same row pattern as scripts/check.sh: a table row whose first cell is a backticked name.
ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_functions() -> list[tuple[str, str, typing.Callable[..., object]]]:
    """Return ``(name, module name, function)`` for every public function of textkit."""
    found = []
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Names imported from elsewhere (``from x import f``) belong to their own module.
            if func.__module__ == module.__name__ and not name.startswith("_"):
                found.append((name, module.__name__, func))
    return found


class PublicApiContractTest(unittest.TestCase):
    """Docstrings, type hints and the README table for every discovered public function."""

    # Show the whole README-table diff: the extra or missing row is what the author needs.
    maxDiff = None

    def setUp(self) -> None:
        self.functions = _public_functions()
        # Guard against a discovery bug that would make every other assertion vacuous.
        self.assertTrue(self.functions, "no public functions discovered in textkit")

    def test_every_public_function_has_a_docstring(self) -> None:
        for name, module, func in self.functions:
            with self.subTest(function=f"{module}.{name}"):
                self.assertTrue((func.__doc__ or "").strip(), "missing docstring")

    def test_every_public_function_is_fully_type_hinted(self) -> None:
        for name, module, func in self.functions:
            with self.subTest(function=f"{module}.{name}"):
                # get_type_hints evaluates the annotations, so one that does not work on the
                # running Python (``X | Y`` on 3.9, say) fails here, not only at call time.
                try:
                    hints = typing.get_type_hints(func)
                except Exception as exc:  # any evaluation error is a contract failure
                    self.fail(f"annotations do not evaluate: {exc!r}")
                params = inspect.signature(func).parameters
                missing = [p for p in params if p not in hints]
                self.assertEqual(missing, [], "parameters without a type hint")
                self.assertIn("return", hints, "no return type hint")

    def test_discovered_functions_equal_the_readme_table(self) -> None:
        discovered = sorted((name, module) for name, module, _ in self.functions)
        # Sorted lists, not sets, so that a duplicated README row also fails.
        table = sorted(ROW.findall(README.read_text(encoding="utf-8")))
        self.assertEqual(discovered, table)


if __name__ == "__main__":
    unittest.main()
