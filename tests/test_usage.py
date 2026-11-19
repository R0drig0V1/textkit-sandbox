"""Runs the usage guide as a doctest and checks it covers the API (plan task T2.8).

``docs/usage.md`` holds one short ``>>>`` example per public function. Two things are
checked:

- every example runs and prints what the guide says: the file is added to the suite as a
  ``doctest.DocFileSuite`` through the ``load_tests`` hook, so a wrong example is a failing
  test (``doctest.testfile`` alone only prints failures and would leave the run green);
- every public function is *called* in at least one ``>>>`` line (``\\b<f>\\(``). The
  ``from textkit.<module> import <f>`` line does not count, so a guide that only imports a
  function still fails.

Nothing is hard-coded: public functions are discovered at run time with the phase 1
definition, as in ``tests/test_api.py``, so a function added later fails this test until it
gets an example.
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
# A doctest source line: ">>> " (or a bare ">>>") after optional indentation.
PROMPT = re.compile(r"^\s*>>>(?: (.*))?$", re.M)


def _public_function_names() -> list[str]:
    """Return the name of every public function of textkit (phase 1 definition)."""
    names = []
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Names imported from elsewhere (``from x import f``) belong to their own module.
            if func.__module__ == module.__name__ and not name.startswith("_"):
                names.append(name)
    return sorted(names)


class UsageGuideCoverageTest(unittest.TestCase):
    """Every discovered public function is called in at least one example of the guide."""

    def test_every_public_function_is_called_in_an_example(self) -> None:
        names = _public_function_names()
        # Guard against a discovery bug that would make the assertion vacuous.
        self.assertTrue(names, "no public functions discovered in textkit")
        source = "\n".join(m.group(1) or "" for m in PROMPT.finditer(USAGE.read_text("utf-8")))
        uncalled = [n for n in names if not re.search(rf"\b{re.escape(n)}\(", source)]
        self.assertEqual(uncalled, [], f"public functions with no example in {USAGE.name}")


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add the doctests of ``docs/usage.md`` to this module's tests (unittest protocol)."""
    tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8"))
    return tests


if __name__ == "__main__":
    unittest.main()
