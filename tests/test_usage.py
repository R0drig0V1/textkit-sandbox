"""Runs the usage guide, ``docs/usage.md``, as a doctest (plan task T2.8).

Two things are checked:

- every example in the guide runs and prints what the guide says: ``load_tests`` adds the
  file as a ``doctest.DocFileSuite``, so a failing example is a failing unittest test (and
  ``scripts/check.sh`` turns red), not just a printed report;
- every public function is called in at least one ``>>>`` line of the guide, so a new
  function cannot ship without an example. An import line does not count: the line must
  contain a call, ``<name>(``.

Public functions are discovered by ``tests/test_api.py`` (the phase 1 definition), so this
file holds no list of names.
"""

import doctest
import pathlib
import re
import unittest

from tests.test_api import _public_functions

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"

# A doctest source line: optional indentation, then the ">>> " prompt.
_PROMPT = re.compile(r"^\s*>>> ?(.*)$", re.M)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add the guide's examples to the tests unittest found in this module."""
    # module_relative=False: the path is absolute, not relative to this module's package.
    tests.addTest(doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8"))
    return tests


class UsageGuideCoverageTest(unittest.TestCase):
    def setUp(self):
        text = USAGE.read_text(encoding="utf-8")
        self.prompt_lines = _PROMPT.findall(text)
        self.names = {qualname.rsplit(".", 1)[1] for qualname in _public_functions()}

    def test_guide_has_examples(self):
        # Guards the coverage test (and the doctest suite) against passing vacuously.
        self.assertTrue(self.prompt_lines)
        self.assertTrue(self.names)

    def test_every_public_function_is_called_in_an_example(self):
        missing = sorted(
            name
            for name in self.names
            if not any(re.search(rf"\b{name}\(", line) for line in self.prompt_lines)
        )
        self.assertEqual(missing, [], "public functions with no example in docs/usage.md")


if __name__ == "__main__":
    unittest.main()
