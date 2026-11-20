"""API contract test (plan task T2.5): every public function is documented and fully typed.

Nothing here is a hard-coded list. Modules are discovered with ``pkgutil.iter_modules`` and
functions with ``inspect.getmembers``, applying the public-function definition of phase 1
("Rules for every task" in docs/phases/phase-1-core-helpers.md): a top-level ``def`` whose
name does not start with ``_``, in a module of ``textkit/`` whose name does not start with
``_``. Hints are read with ``typing.get_type_hints``, so an annotation that does not evaluate
on the running Python (``X | Y`` on 3.9, say) fails here instead of only at call time.
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
_README_ROW = re.compile(r"^\| `(\w+)` \| `([\w.]+)` \|", re.M)


def _public_modules() -> list[ModuleType]:
    """Import and return every public module of ``textkit`` (name not starting with ``_``)."""
    return [
        importlib.import_module(f"{textkit.__name__}.{info.name}")
        for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_")
    ]


def _public_functions(module: ModuleType) -> list[FunctionType]:
    """Return the public functions defined in ``module`` itself.

    The ``__module__`` filter drops functions a module merely imports (``from x import f``),
    which belong to the module that defines them.
    """
    return [
        f
        for name, f in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_") and f.__module__ == module.__name__
    ]


def _contract_problems(f: FunctionType) -> list[str]:
    """Return what ``f`` lacks under the API contract; ``[]`` when it complies.

    The contract: a non-empty docstring, and a type hint for every parameter (``*args`` and
    ``**kwargs`` included) and for the return value. A hint that cannot be evaluated is
    reported as a problem rather than raised, so one bad function does not hide the others.
    """
    problems = []
    if not (f.__doc__ or "").strip():
        problems.append("no docstring")
    try:
        hints = typing.get_type_hints(f)
    except Exception as exc:  # NameError, TypeError, SyntaxError from a bad annotation
        return problems + [f"type hints do not evaluate: {type(exc).__name__}: {exc}"]
    for param in inspect.signature(f).parameters:
        if param not in hints:
            problems.append(f"parameter {param!r} has no type hint")
    if "return" not in hints:
        problems.append("no return type hint")
    return problems


class ApiContractTest(unittest.TestCase):
    """Every public function of every public module complies with the API contract."""

    def test_discovery_finds_functions(self):
        # Guards against a vacuous pass: if discovery broke, every other check would see
        # nothing and succeed.
        self.assertTrue(_public_modules())
        self.assertTrue([f for m in _public_modules() for f in _public_functions(m)])

    def test_every_public_function_has_docstring_and_type_hints(self):
        for module in _public_modules():
            for f in _public_functions(module):
                with self.subTest(function=f"{module.__name__}.{f.__name__}"):
                    self.assertEqual(_contract_problems(f), [])

    def test_discovered_functions_equal_readme_table(self):
        discovered = {
            (f.__name__, module.__name__)
            for module in _public_modules()
            for f in _public_functions(module)
        }
        table = set(_README_ROW.findall(README.read_text(encoding="utf-8")))
        self.assertEqual(discovered, table)


class ContractProblemsTest(unittest.TestCase):
    """The checker itself reports each kind of violation, so a pass above means something."""

    def test_compliant_function_has_no_problems(self):
        def ok(text: str, *args: int, flag: bool = False, **kwargs: str) -> str:
            """Documented."""
            return text

        self.assertEqual(_contract_problems(ok), [])

    def test_missing_docstring(self):
        def f(text: str) -> str:
            return text

        self.assertEqual(_contract_problems(f), ["no docstring"])

    def test_missing_parameter_and_return_hints(self):
        def f(text, *args, **kwargs):
            """Documented."""

        self.assertEqual(
            _contract_problems(f),
            [
                "parameter 'text' has no type hint",
                "parameter 'args' has no type hint",
                "parameter 'kwargs' has no type hint",
                "no return type hint",
            ],
        )

    def test_unevaluable_hint_is_a_problem(self):
        def f(text: "NoSuchType") -> str:  # noqa: F821 - the point of the test
            """Documented."""
            return text

        problems = _contract_problems(f)
        self.assertEqual(len(problems), 1)
        self.assertIn("type hints do not evaluate: NameError", problems[0])


if __name__ == "__main__":
    unittest.main()
