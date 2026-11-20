"""Usage guide test (plan task T2.8): docs/usage.md runs, and it covers every public function.

The ``load_tests`` hook adds every ``>>>`` example of docs/usage.md to the suite as a doctest
(``doctest.DocFileSuite``), so a wrong example fails ``scripts/check.sh`` like any other test.
``UsageCoverageTest`` checks that the guide calls each public function in at least one
``>>>`` line. Public functions are discovered, never listed by hand, with the definition of
phase 1 ("Rules for every task" in docs/phases/phase-1-core-helpers.md), the same one
tests/test_api.py applies.
"""

import doctest
import importlib
import inspect
import pathlib
import pkgutil
import re
import unittest

import textkit

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"


def _public_function_names() -> list[str]:
    """Return the names of every public function of ``textkit``, sorted.

    A public function is a top-level function whose name does not start with ``_``, defined
    (``__module__`` filter, so imports are not counted twice) in a module of ``textkit``
    whose name does not start with ``_``.
    """
    names = []
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        names.extend(
            name
            for name, f in inspect.getmembers(module, inspect.isfunction)
            if not name.startswith("_") and f.__module__ == module.__name__
        )
    return sorted(names)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """unittest hook: add the doctests of docs/usage.md to this module's tests.

    ``module_relative=False`` because the path is absolute; ``encoding="utf-8"`` because the
    guide has non-ASCII examples and the default would be the locale's encoding.
    """
    tests.addTests(
        doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8")
    )
    return tests


class UsageCoverageTest(unittest.TestCase):
    """Every public function is called in at least one ``>>>`` line of docs/usage.md."""

    def test_guide_has_examples(self) -> None:
        # Guards against a DocFileSuite that silently runs nothing (an empty or moved file).
        parser = doctest.DocTestParser()
        examples = parser.get_examples(USAGE.read_text(encoding="utf-8"))
        self.assertGreater(len(examples), 0)

    def test_every_public_function_is_called(self) -> None:
        prompts = [
            line.strip()[4:]
            for line in USAGE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(">>> ")
        ]
        functions = _public_function_names()
        self.assertTrue(functions, "no public functions discovered")
        missing = [
            f
            for f in functions
            if not any(re.search(rf"\b{re.escape(f)}\(", p) for p in prompts)
        ]
        self.assertEqual(missing, [], "public functions without an example in docs/usage.md")


if __name__ == "__main__":
    unittest.main()
