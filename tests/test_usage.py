"""Tests for docs/usage.md, the usage guide (plan task T2.8).

Every ``>>>`` example of the guide runs as a doctest: ``load_tests`` adds
``doctest.DocFileSuite`` to this module's tests, so a wrong example fails the unit tests (and
``scripts/check.sh``) instead of only printing a report, as a bare ``doctest.testfile`` would.

The guide must also call every public function at least once on a ``>>>`` line. An import
line alone does not count: the call regex is ``\\b<name>\\(``. The public functions are
discovered at run time with the definition of docs/phases/phase-1-core-helpers.md ("Rules
for every task"), the same discovery as tests/test_api.py, so a new function fails here until
the guide shows it.
"""

import doctest
import importlib
import inspect
import pathlib
import pkgutil
import re
import unittest

import textkit

_USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add the doctests of docs/usage.md to the tests of this module (unittest protocol)."""
    tests.addTests(doctest.DocFileSuite(str(_USAGE), module_relative=False, encoding="utf-8"))
    return tests


def _public_function_names() -> set[str]:
    """Return the names of every public function of ``textkit`` (phase 1 definition)."""
    names = set()
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ == module.__name__ and not name.startswith("_"):
                names.add(name)
    return names


def _source_lines(text: str) -> list[str]:
    """Return the source of every ``>>>`` line of ``text``, without the prompt."""
    return [line.strip()[4:] for line in text.splitlines() if line.strip().startswith(">>> ")]


class UsageGuideTest(unittest.TestCase):
    """docs/usage.md has runnable examples and shows every public function."""

    def setUp(self) -> None:
        self.text = _USAGE.read_text(encoding="utf-8")

    def test_guide_has_examples(self) -> None:
        # A guide whose examples doctest cannot parse would pass DocFileSuite vacuously.
        examples = doctest.DocTestParser().get_examples(self.text)
        self.assertGreater(len(examples), 0, "docs/usage.md has no doctest examples")

    def test_discovery_finds_functions(self) -> None:
        self.assertTrue(_public_function_names(), "no public functions discovered in textkit")

    def test_every_public_function_is_called(self) -> None:
        sources = _source_lines(self.text)
        for name in sorted(_public_function_names()):
            with self.subTest(function=name):
                call = re.compile(rf"\b{re.escape(name)}\(")
                self.assertTrue(
                    any(call.search(line) for line in sources),
                    f"docs/usage.md never calls {name}() on a >>> line",
                )

    def test_import_line_alone_does_not_count(self) -> None:
        # The checker itself: an import names the function but does not call it.
        sources = _source_lines(">>> from textkit.strings import slugify\n")
        self.assertFalse(any(re.search(r"\bslugify\(", line) for line in sources))


if __name__ == "__main__":
    unittest.main()
