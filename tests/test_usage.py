"""Usage guide test (plan task T2.8): runs every example in ``docs/usage.md`` and checks that
every public function has one.

The examples run as doctests through the ``load_tests`` hook below, so a wrong example fails
``python3 -m unittest discover`` (and with it ``scripts/check.sh``). The coverage check finds
the public functions with the same discovery as the API contract test (``tests/test_api.py``,
phase 1 definition of a public function), never from a hard-coded list, so a new function
without an example in the guide fails here.
"""

import doctest
import pathlib
import re
import unittest

from tests.test_api import _public_functions

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"


def load_tests(loader, tests, pattern):
    """Add the doctests of ``docs/usage.md`` to the tests unittest found in this module."""
    tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False))
    return tests


def _example_sources() -> list:
    """Return the source of every example doctest will run in the guide, one per ``>>>``.

    Parsing with ``DocTestParser`` (rather than grepping the text) counts only what doctest
    actually executes, so a ``>>>`` it would not pick up cannot satisfy the coverage check.
    """
    text = USAGE.read_text(encoding="utf-8")
    return [ex.source for ex in doctest.DocTestParser().get_examples(text, str(USAGE))]


class UsageGuideTest(unittest.TestCase):
    def setUp(self):
        self.functions = _public_functions()
        self.sources = _example_sources()

    def test_guide_has_examples(self):
        # Guards against a parse problem that leaves nothing to run and makes the doctest
        # suite pass vacuously.
        self.assertTrue(self.sources, f"no doctest examples found in {USAGE}")

    def test_every_public_function_is_called_in_an_example(self):
        self.assertTrue(self.functions, "no public functions discovered in textkit")
        for name in self.functions:
            with self.subTest(function=name):
                call = re.compile(rf"\b{re.escape(name)}\(")
                self.assertTrue(
                    any(call.search(src) for src in self.sources),
                    f"no '>>> ... {name}(' example in docs/usage.md",
                )

    def test_examples_import_from_the_defining_module(self):
        # The guide tells readers where each function lives: ``from textkit.counts import
        # word_count`` must name the module that defines ``word_count``.
        imports = re.compile(r"^from (textkit\.\w+) import (.+)$")
        for src in self.sources:
            match = imports.match(src.strip())
            if not match:
                continue
            module, names = match.groups()
            for name in (n.strip() for n in names.split(",")):
                if name in self.functions:
                    with self.subTest(function=name):
                        self.assertEqual(module, self.functions[name].__module__)


if __name__ == "__main__":
    unittest.main()
