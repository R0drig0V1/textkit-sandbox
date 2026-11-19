"""Usage guide test (plan task T2.8, docs/phases/phase-2-tools.md).

``docs/usage.md`` holds one doctest example per public function. This module makes
``unittest`` run that file as a doctest, through the ``load_tests`` hook, so a wrong example
turns ``scripts/check.sh`` red; and it checks that every public function is called in at
least one ``>>>`` line, so a function added later without an example fails too.

Public functions are discovered with the helpers of ``tests/test_api.py`` (the phase-1
definition: a top-level ``def`` not starting with ``_``, in a module of ``textkit/`` not
starting with ``_``), so nothing is hard-coded here.
"""

import doctest
import pathlib
import re
import unittest

from tests.test_api import public_functions, public_modules

USAGE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"


def _source_lines(text: str) -> list[str]:
    """Return the ``>>>`` lines of ``text``, without the prompt.

    Only ``>>>`` lines count as calls: a function named in prose or in an expected output
    does not prove the guide exercises it.
    """
    return [m.group(1) for m in re.finditer(r"^\s*>>> (.*)$", text, re.M)]


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add ``docs/usage.md`` as a doctest to this module's tests.

    ``encoding`` is explicit because the guide contains non-ASCII examples and doctest
    would otherwise read it with the locale's encoding.
    """
    tests.addTests(
        doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8")
    )
    return tests


class UsageGuideTest(unittest.TestCase):
    """The guide covers every public function, with examples doctest actually runs."""

    def setUp(self) -> None:
        self.text = USAGE.read_text(encoding="utf-8")
        self.functions = sorted(
            (module.__name__, name)
            for module in public_modules()
            for name in public_functions(module)
        )

    def test_discovers_functions(self) -> None:
        # Guards against discovery finding nothing, which would make the coverage test vacuous.
        self.assertTrue(self.functions, "no public function discovered in textkit")

    def test_guide_has_examples(self) -> None:
        # A guide whose examples doctest does not parse (no ">>> " prompt, for example) would
        # make the doctest pass while running nothing.
        examples = doctest.DocTestParser().get_examples(self.text)
        self.assertGreater(len(examples), 0, f"no doctest example in {USAGE}")

    def test_every_public_function_is_called(self) -> None:
        source = "\n".join(_source_lines(self.text))
        for module, name in self.functions:
            with self.subTest(function=f"{module}.{name}"):
                # re.search rather than assertRegex, whose message would dump every line.
                self.assertIsNotNone(
                    re.search(rf"\b{re.escape(name)}\(", source),
                    f"{name} is not called in any '>>>' line of {USAGE}",
                )

    def test_every_public_function_is_imported_from_its_module(self) -> None:
        # The guide's convention: each example starts with ">>> from textkit.<module> import
        # <f>", so a reader copying one example gets the right import.
        source = "\n".join(_source_lines(self.text))
        for module, name in self.functions:
            with self.subTest(function=f"{module}.{name}"):
                line = rf"(?m)^from {re.escape(module)} import {re.escape(name)}$"
                self.assertIsNotNone(
                    re.search(line, source),
                    f"no '>>> from {module} import {name}' line in {USAGE}",
                )


if __name__ == "__main__":
    unittest.main()
