"""Tests for the usage guide, docs/usage.md (plan task T2.8).

Two things are checked:

1. Every ``>>>`` example in the guide runs and prints what it says. The guide is loaded as a
   ``doctest.DocFileSuite`` through the ``load_tests`` hook, so each failing example is a
   failing unittest and turns ``scripts/check.sh`` red (``doctest.testfile`` alone only
   prints failures and would never fail the run).
2. Every public function is called in at least one ``>>>`` line (``\\b<name>\\(``); an
   import line alone does not count. Public functions are found by parsing ``textkit/`` with
   ``ast``, the way ``scripts/check.sh`` does (definition in
   docs/phases/phase-1-core-helpers.md: a top-level ``def`` whose name does not start with
   ``_``, in a module whose name does not start with ``_``), so a new function without an
   example fails here.
"""

import ast
import doctest
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
USAGE = ROOT / "docs" / "usage.md"

# A doctest source line: optional indentation, then ">>>" (the same anchor doctest uses).
_PROMPT_LINE = re.compile(r"^\s*>>>(.*)$", re.M)


def public_functions() -> list:
    """Return the sorted names of every public function of ``textkit``."""
    return sorted(
        node.name
        for path in (ROOT / "textkit").glob("*.py")
        if not path.name.startswith("_")
        for node in ast.parse(path.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    )


def load_tests(loader, tests, pattern):
    """Add every example of docs/usage.md to this module's tests (unittest's hook)."""
    # encoding is explicit: the guide holds non-ASCII examples ("Ñandú") and the default
    # would follow the locale, which differs between machines and CI.
    tests.addTests(doctest.DocFileSuite(str(USAGE), module_relative=False, encoding="utf-8"))
    return tests


class UsageGuideCoverageTest(unittest.TestCase):
    """docs/usage.md shows every public function in a ``>>>`` line."""

    def test_every_public_function_is_called(self):
        prompts = _PROMPT_LINE.findall(USAGE.read_text(encoding="utf-8"))
        self.assertTrue(prompts, "docs/usage.md has no >>> examples")
        missing = [
            name
            for name in public_functions()
            if not any(re.search(rf"\b{name}\(", line) for line in prompts)
        ]
        self.assertEqual(missing, [], "public functions with no >>> call in docs/usage.md")

    def test_discovery_finds_functions(self):
        # Guards the check above: if discovery broke and found nothing, it would pass vacuously.
        self.assertIn("slugify", public_functions())


if __name__ == "__main__":
    unittest.main()
