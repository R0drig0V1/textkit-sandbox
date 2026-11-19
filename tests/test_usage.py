"""Usage guide test (plan task T2.8): docs/usage.md runs, and covers every public function.

``load_tests`` adds docs/usage.md as a ``doctest.DocFileSuite``, so every ``>>>`` example in
the guide runs with the unit tests (and therefore in ``scripts/check.sh``). ``UsageGuideTest``
then checks that each public function is called in at least one ``>>>`` line, so a function
merged later without an example turns the checks red.

Nothing is hard-coded: "public function" follows the definition in
docs/phases/phase-1-core-helpers.md ("Rules for every task"), a top-level ``def`` whose name
does not start with ``_`` in a ``textkit`` module whose name does not start with ``_``, and
is discovered at run time. Private modules and ``__main__`` are never imported here.
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


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add the doctest examples of docs/usage.md to this module's tests.

    ``module_relative=False`` makes the path absolute rather than relative to this package,
    so the guide is found wherever the tests are run from.
    """
    tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False))
    return tests


def _public_function_names() -> list[str]:
    """Return the names of all public functions of ``textkit``, sorted.

    Names starting with ``_`` are filtered out *before* importing, so ``textkit.__main__``
    is never imported (and the command line never runs). ``f.__module__`` drops names a
    module merely imports, so each function is counted where it is defined.
    """
    names = set()
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ == module.__name__ and not name.startswith("_"):
                names.add(name)
    return sorted(names)


def _prompt_lines(text: str) -> list[str]:
    """Return the source lines of ``text`` that start a doctest example (``>>>``)."""
    return [line.strip() for line in text.splitlines() if line.lstrip().startswith(">>>")]


class UsageGuideTest(unittest.TestCase):
    """docs/usage.md has runnable examples and calls every public function."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = USAGE.read_text(encoding="utf-8")
        cls.prompts = _prompt_lines(cls.text)

    def test_guide_has_examples(self) -> None:
        examples = doctest.DocTestParser().get_examples(self.text)
        self.assertGreater(len(examples), 0)

    def test_public_functions_found(self) -> None:
        # Guards the coverage test below against passing vacuously if discovery breaks.
        self.assertGreater(len(_public_function_names()), 0)

    def test_every_public_function_is_called(self) -> None:
        missing = [
            name for name in _public_function_names()
            if not any(re.search(rf"\b{re.escape(name)}\(", line) for line in self.prompts)
        ]
        self.assertEqual(missing, [], f"public functions with no '>>>' call in {USAGE}")


if __name__ == "__main__":
    unittest.main()
