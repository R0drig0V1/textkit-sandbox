"""Tests for the package textkit/diff/ as a whole (plan task T3.6).

The module tests are in ``tests/test_diff_<module>.py``; this file checks what the package
promises: its public functions, where ``PatchError`` lives, and that no module of
``textkit/`` uses ``difflib`` (the plan asks for an LCS of our own).
"""

import ast
import pathlib
import unittest

import textkit.diff
from textkit.errors import InvalidValueError

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageTest(unittest.TestCase):
    def test_public_functions(self):
        self.assertEqual(textkit.diff.__all__, ["apply_patch", "diff_words", "unified_diff"])
        for name in textkit.diff.__all__:
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(textkit.diff, name)))

    def test_patch_error_is_importable_but_not_public(self):
        from textkit.diff import PatchError

        self.assertTrue(issubclass(PatchError, InvalidValueError))
        self.assertFalse(issubclass(PatchError, ValueError))
        self.assertNotIn("PatchError", textkit.diff.__all__)

    def test_no_difflib_in_textkit(self):
        sources = sorted((ROOT / "textkit").rglob("*.py"))
        self.assertIn(ROOT / "textkit" / "diff" / "lcs.py", sources)
        for path in sources:
            with self.subTest(path=str(path.relative_to(ROOT))):
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    self.assertFalse(
                        any(n.split(".")[0] == "difflib" for n in names), f"difflib in {path}"
                    )


if __name__ == "__main__":
    unittest.main()
