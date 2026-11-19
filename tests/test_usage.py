"""The usage guide runs (plan task T2.8): every example in docs/usage.md is a doctest.

The ``load_tests`` hook adds docs/usage.md as a ``doctest.DocFileSuite``, so a wrong example
is a failing unittest and turns ``scripts/check.sh`` red (``doctest.testfile`` alone only
prints failures). ``UsageCoverageTest`` checks that the guide calls every public function in
at least one ``>>>`` line: an import line alone does not count, since it runs nothing. The
public functions are discovered by ``tests/test_api.py`` with the phase 1 definition, never
listed here, so a new function fails this test until the guide shows it.
"""

import doctest
import pathlib
import re
import unittest

from tests.test_api import _public_functions

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"

# The source of a doctest example: what follows ">>> " on its line.
_PROMPT_LINE = re.compile(r"^\s*>>> (.*)$", re.M)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str
) -> unittest.TestSuite:
    """Add the examples of docs/usage.md to this module's tests (the unittest protocol)."""
    tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8"))
    return tests


class UsageCoverageTest(unittest.TestCase):
    """docs/usage.md calls every public function of textkit in a ``>>>`` line."""

    def test_every_public_function_is_called(self) -> None:
        calls = "\n".join(_PROMPT_LINE.findall(USAGE.read_text(encoding="utf-8")))
        names = sorted({name for _, name, _ in _public_functions()})
        # Guards against passing vacuously if discovery ever breaks.
        self.assertTrue(names, "no public function discovered in textkit")
        missing = [name for name in names if not re.search(rf"\b{name}\(", calls)]
        self.assertEqual(missing, [], f"docs/usage.md never calls {missing} in a >>> line")


if __name__ == "__main__":
    unittest.main()
