"""API contract test for textkit (plan task T2.5).

Every public function of every textkit module must have a docstring and type hints for all
of its parameters and its return value, and the set of public functions must equal the
README function table. Nothing is hard-coded: modules and functions are discovered at run
time, so functions added later are checked without editing this file.

"Public function" is the phase-1 definition (docs/phases/phase-1-core-helpers.md, "Rules
for every task"): a top-level def whose name does not start with ``_``, in a module of
``textkit/`` whose name does not start with ``_``.
"""

import importlib
import inspect
import pathlib
import pkgutil
import re
import typing
import unittest
from typing import Callable, Dict, List, Set, Tuple

import textkit

README = pathlib.Path(__file__).resolve().parents[1] / "README.md"

# A README table row starts with "| `name` | `module` |" (the same row shape that
# scripts/check.sh parses, plus the module column).
ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_functions() -> Dict[Tuple[str, str], Callable[..., object]]:
    """Map (module name, function name) to every public function of textkit.

    Modules come from ``pkgutil.iter_modules(textkit.__path__)``; functions from
    ``inspect.getmembers(m, inspect.isfunction)`` keeping those defined in ``m`` itself
    (``f.__module__ == m.__name__``), so names imported from other modules are skipped.
    """
    found = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ == module.__name__ and not name.startswith("_"):
                found[(module.__name__, name)] = func
    return found


def _contract_problems(func: Callable[..., object]) -> List[str]:
    """Return what ``func`` lacks to meet the contract (empty when it meets it).

    Hints are read with ``typing.get_type_hints``, so an annotation that does not evaluate
    on the running Python (``int | None`` on 3.9, a misspelt name) is reported, not skipped.
    """
    problems = []
    if not (func.__doc__ or "").strip():
        problems.append("no docstring")
    try:
        hints = typing.get_type_hints(func)
    except Exception as exc:  # any evaluation error means the annotations are broken
        return problems + [f"type hints do not evaluate: {exc!r}"]
    for param in inspect.signature(func).parameters:
        if param not in hints:
            problems.append(f"no type hint for parameter {param!r}")
    if "return" not in hints:
        problems.append("no return type hint")
    return problems


def _readme_rows() -> List[Tuple[str, str]]:
    """Return the (module, function) pairs of the README function table, in order."""
    return [(module, name) for name, module in ROW.findall(README.read_text(encoding="utf-8"))]


class ApiContractTest(unittest.TestCase):
    def setUp(self):
        self.functions = _public_functions()

    def test_discovers_functions(self):
        # Guards against discovery silently finding nothing (which would pass every check).
        self.assertTrue(self.functions)

    def test_every_public_function_meets_the_contract(self):
        failures = {
            f"{module}.{name}": problems
            for (module, name), func in sorted(self.functions.items())
            if (problems := _contract_problems(func))
        }
        self.assertEqual(failures, {})

    def test_discovered_set_equals_readme_table(self):
        rows = _readme_rows()
        self.assertEqual(len(rows), len(set(rows)), "README table has duplicate rows")
        discovered: Set[Tuple[str, str]] = set(self.functions)
        self.assertEqual(discovered, set(rows))


class ContractCheckerTest(unittest.TestCase):
    """The checker itself flags each kind of violation (so a green run means something)."""

    def test_complete_function_passes(self):
        def good(text: str, width: int = 1) -> str:
            """Documented."""
            return text

        self.assertEqual(_contract_problems(good), [])

    def test_missing_docstring(self):
        def bad(text: str) -> str:
            return text

        self.assertEqual(_contract_problems(bad), ["no docstring"])

    def test_missing_parameter_and_return_hints(self):
        def bad(text, width: int):
            """Documented."""
            return text

        self.assertEqual(
            _contract_problems(bad),
            ["no type hint for parameter 'text'", "no return type hint"],
        )

    def test_annotation_that_does_not_evaluate(self):
        def bad(text: "NoSuchType") -> str:  # noqa: F821
            """Documented."""
            return text

        problems = _contract_problems(bad)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("type hints do not evaluate"))


if __name__ == "__main__":
    unittest.main()
