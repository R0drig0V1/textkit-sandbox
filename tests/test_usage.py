"""Usage guide test (plan task T2.8): runs every example in ``docs/usage.md`` and checks coverage.

The examples are doctests. They are added to the unittest run through the ``load_tests`` hook
as a ``doctest.DocFileSuite``, so a wrong example fails ``unittest`` (and ``scripts/check.sh``)
like any other test; ``doctest.testfile`` alone would only print the failure.

Coverage: every public function must be *called* in at least one ``>>>`` line
(``\\b<name>\\(``), so the import line of an example does not count on its own. Public functions
are discovered with the phase 1 definition (docs/phases/phase-1-core-helpers.md, "Rules for
every task") through ``tests.test_api._public_functions``, the same discovery the API contract
test uses, so a function added later needs an example here without editing this file.
"""

import doctest
import pathlib
import re
import unittest
from typing import Iterable

from tests.test_api import _public_functions

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"

# The source of a doctest example: a line whose first non-blank characters are ">>> ".
PROMPT_LINE = re.compile(r"^\s*>>> (.*)$", re.M)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add the doctests of ``docs/usage.md`` to the tests unittest found in this module."""
    # encoding is explicit so the accented examples read the same under any locale.
    tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8"))
    return tests


def _uncalled(names: Iterable[str], text: str) -> list[str]:
    """Return the ``names`` that no ``>>>`` line of ``text`` calls, sorted."""
    sources = "\n".join(PROMPT_LINE.findall(text))
    return sorted(n for n in names if not re.search(rf"\b{re.escape(n)}\(", sources))


class UsageGuideTest(unittest.TestCase):
    """``docs/usage.md`` has a runnable example calling each public function."""

    def test_usage_has_examples(self) -> None:
        # Guards the doctest suite against passing vacuously on a page with no examples.
        examples = doctest.DocTestParser().get_examples(USAGE.read_text(encoding="utf-8"))
        self.assertTrue(examples)

    def test_every_public_function_is_called(self) -> None:
        names = [f.__name__ for f in _public_functions()]
        self.assertTrue(names)
        self.assertEqual(_uncalled(names, USAGE.read_text(encoding="utf-8")), [])


class UncalledTest(unittest.TestCase):
    """The coverage checker itself, so a green coverage test means something."""

    def test_an_import_alone_is_not_a_call(self) -> None:
        text = ">>> from textkit.strings import slugify, squeeze\n>>> squeeze(' a ')\n'a'\n"
        self.assertEqual(_uncalled(["slugify", "squeeze"], text), ["slugify"])

    def test_a_call_outside_a_prompt_line_does_not_count(self) -> None:
        self.assertEqual(_uncalled(["wrap"], "Use wrap(text, 10) to split.\n"), ["wrap"])

    def test_a_longer_name_does_not_cover_a_shorter_one(self) -> None:
        # "slug_title(" must not count as a call of a function named "title".
        self.assertEqual(_uncalled(["title"], ">>> slug_title('a b', 3)\n"), ["title"])

    def test_a_nested_call_counts(self) -> None:
        self.assertEqual(_uncalled(["slugify"], ">>> len(slugify('a b'))\n"), [])


if __name__ == "__main__":
    unittest.main()
