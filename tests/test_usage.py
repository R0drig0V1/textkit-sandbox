"""Tests for the usage guide docs/usage.md (plan task T2.8).

Two checks, so the guide can neither rot nor fall behind the package:

- every ``>>>`` example in ``docs/usage.md`` runs as a doctest (added to this module's suite
  by the ``load_tests`` hook), so a wrong example makes ``scripts/check.sh`` red;
- every public function is called in at least one ``>>>`` line (``\\b<f>\\(``), so a
  function added later without an example fails here, naming it.

Public functions are discovered at run time with the same helper as the API contract test
(``tests/test_api.py``, phase-1 definition of "public function"), never hard-coded.
"""

import doctest
import pathlib
import re
import unittest
from typing import List, Optional

from tests.test_api import _public_functions

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"

# A doctest source line: optional indentation, then the ">>>" prompt. Continuation lines
# ("...") are not counted, as the plan asks for a call on a ">>>" line.
PROMPT = re.compile(r"^\s*>>>(.*)$", re.M)


def load_tests(
    loader: unittest.TestLoader, standard_tests: unittest.TestSuite, pattern: Optional[str]
) -> unittest.TestSuite:
    """Return this module's test cases plus one doctest case for ``docs/usage.md``.

    ``module_relative=False`` makes the absolute path work wherever the tests are run from.
    """
    standard_tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False))
    return standard_tests


def _prompt_lines() -> List[str]:
    """Return the source of every ``>>>`` line of the usage guide, without the prompt."""
    return PROMPT.findall(USAGE.read_text(encoding="utf-8"))


class UsageGuideTest(unittest.TestCase):
    """docs/usage.md has examples, and one calling every public function."""

    def test_guide_has_examples(self) -> None:
        # Guards against an empty (or wrongly fenced) guide passing the doctest vacuously.
        self.assertTrue(_prompt_lines(), f"no >>> examples in {USAGE}")

    def test_every_public_function_is_called(self) -> None:
        names = sorted({name for _module, name in _public_functions()})
        self.assertTrue(names, "no public functions discovered")
        lines = _prompt_lines()
        missing = [
            name
            for name in names
            if not any(re.search(rf"\b{re.escape(name)}\(", line) for line in lines)
        ]
        self.assertEqual(missing, [], f"public functions with no example in {USAGE}")


if __name__ == "__main__":
    unittest.main()
