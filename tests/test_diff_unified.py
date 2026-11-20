"""Tests for textkit/diff/unified.py: ``unified_diff`` and ``split_lines`` (plan task T3.6).

``GNU_CASES`` compares ``unified_diff`` byte for byte with the real tool on cases whose
shortest edit is unique (so any correct LCS gives the same script).
"""

import random
import unittest

from textkit.diff import unified_diff as package_unified_diff
from textkit.diff.unified import NO_NEWLINE, split_lines, unified_diff
from textkit.errors import InvalidValueError


def _lines(*items):
    return "".join(f"{item}\n" for item in items)


_ONE_TO_20 = _lines(*range(1, 21))

# Captured once with `git diff --no-index --no-color -U<context> a b` from
# git version 2.54.0 (Apple Git-157), which numbers hunks as GNU diffutils' `diff -u` does
# (an empty range at the top of a file is 0, not BSD diff's 1). Its "diff --git", "index",
# "---" and "+++" lines were replaced by "--- a" and "+++ b". The files were written with
# newline="" and git ran with core.autocrlf=false, so "\r" reached it unchanged.
# Rows: (name, a, b, context, expected output).
GNU_CASES = [
    ("one changed line", _lines(*range(1, 10)), _lines(1, 2, 3, 4, 50, 6, 7, 8, 9), 3,
     "--- a\n+++ b\n@@ -2,7 +2,7 @@\n 2\n 3\n 4\n-5\n+50\n 6\n 7\n 8\n"),
    ("gap of 2 * context: one hunk", _ONE_TO_20, _ONE_TO_20.replace("\n4\n", "\n40\n")
     .replace("\n11\n", "\n110\n"), 3,
     "--- a\n+++ b\n@@ -1,14 +1,14 @@\n 1\n 2\n 3\n-4\n+40\n 5\n 6\n 7\n 8\n 9\n 10\n"
     "-11\n+110\n 12\n 13\n 14\n"),
    ("gap of 2 * context + 1: two hunks", _ONE_TO_20, _ONE_TO_20.replace("\n4\n", "\n40\n")
     .replace("\n12\n", "\n120\n"), 3,
     "--- a\n+++ b\n@@ -1,7 +1,7 @@\n 1\n 2\n 3\n-4\n+40\n 5\n 6\n 7\n"
     "@@ -9,7 +9,7 @@\n 9\n 10\n 11\n-12\n+120\n 13\n 14\n 15\n"),
    ("no final newline on either side", "1\n2\n3", "1\n2\n4", 3,
     "--- a\n+++ b\n@@ -1,3 +1,3 @@\n 1\n 2\n-3\n\\ No newline at end of file\n"
     "+4\n\\ No newline at end of file\n"),
    ("final newline added", "1\n2", "1\n2\n", 3,
     "--- a\n+++ b\n@@ -1,2 +1,2 @@\n 1\n-2\n\\ No newline at end of file\n+2\n"),
    ("insertion before line 1, context 0", "2\n3\n", "1\n2\n3\n", 0,
     "--- a\n+++ b\n@@ -0,0 +1 @@\n+1\n"),
    ("deletion of line 1, context 0", "1\n2\n", "2\n", 0,
     "--- a\n+++ b\n@@ -1 +0,0 @@\n-1\n"),
    ("insertion after line 1, context 0", "1\n3\n", "1\n2\n3\n", 0,
     "--- a\n+++ b\n@@ -1,0 +2 @@\n+2\n"),
    ("empty to text", "", "1\n2\n", 3, "--- a\n+++ b\n@@ -0,0 +1,2 @@\n+1\n+2\n"),
    ("text to empty", "1\n", "", 3, "--- a\n+++ b\n@@ -1 +0,0 @@\n-1\n"),
    ("CRLF line against LF line", "1\r\n2\n", "1\n2\n", 3,
     "--- a\n+++ b\n@@ -1,2 +1,2 @@\n-1\r\n+1\n 2\n"),
    ("append at the end, context 1", _lines(1, 2, 3, 4, 5), _lines(1, 2, 3, 4, 5, 6), 1,
     "--- a\n+++ b\n@@ -5 +5,2 @@\n 5\n+6\n"),
]


def _hunk_count(diff):
    return sum(line.startswith("@@ ") for line in diff.splitlines())


class SplitLinesTest(unittest.TestCase):
    def test_splits_after_each_newline_only(self):
        self.assertEqual(split_lines("a\r\nb\rc\x0cd\x85e\n"), ["a\r\n", "b\rc\x0cd\x85e\n"])

    def test_last_line_without_newline_and_empty_text(self):
        self.assertEqual(split_lines(""), [])
        self.assertEqual(split_lines("\n"), ["\n"])
        self.assertEqual(split_lines("a\nb"), ["a\n", "b"])

    def test_joining_the_lines_gives_the_text_back(self):
        rng = random.Random(1)
        for _ in range(200):
            text = "".join(rng.choice("ab\n\r") for _ in range(rng.randint(0, 12)))
            with self.subTest(text=text):
                self.assertEqual("".join(split_lines(text)), text)


class GnuComparisonTest(unittest.TestCase):
    def test_matches_gnu_diff_byte_for_byte(self):
        for name, a, b, context, expected in GNU_CASES:
            with self.subTest(name):
                self.assertEqual(
                    unified_diff(a, b, context).encode("utf-8"), expected.encode("utf-8")
                )

    def test_table_holds_the_rows_the_plan_requires(self):
        outputs = {name: expected for name, _, _, _, expected in GNU_CASES}
        self.assertGreaterEqual(len(GNU_CASES), 6)
        self.assertEqual(_hunk_count(outputs["gap of 2 * context: one hunk"]), 1)
        self.assertEqual(_hunk_count(outputs["gap of 2 * context + 1: two hunks"]), 2)
        self.assertIn(NO_NEWLINE, outputs["no final newline on either side"])
        self.assertIn("@@ -0,0 +1 @@\n", outputs["insertion before line 1, context 0"])
        self.assertIn("@@ -1 +0,0 @@\n", outputs["deletion of line 1, context 0"])


class UnifiedDiffTest(unittest.TestCase):
    def test_equal_texts_give_empty_string(self):
        for text in ("", "a\n", "a\nb", "x\r\n"):
            with self.subTest(text=text):
                self.assertEqual(unified_diff(text, text), "")
                self.assertEqual(unified_diff(text, text, 0), "")

    def test_exported_from_the_package(self):
        self.assertIs(package_unified_diff, unified_diff)

    def test_headers_and_default_context_of_three(self):
        a = _lines(*range(1, 11))
        diff = unified_diff(a, a.replace("\n6\n", "\nsix\n"))
        self.assertTrue(diff.startswith("--- a\n+++ b\n@@ -3,7 +3,7 @@\n"))
        self.assertEqual(diff.count("\n "), 6)

    def test_merge_boundary_for_every_context(self):
        # Two changes share a hunk when at most 2 * context unchanged lines separate them.
        for context in range(0, 5):
            for gap in (2 * context, 2 * context + 1):
                lines = [f"{k}\n" for k in range(gap + 2 + 2 * context)]
                a = "".join(lines)
                changed = list(lines)
                changed[context] = "x\n"
                changed[context + gap + 1] = "y\n"
                with self.subTest(context=context, gap=gap):
                    diff = unified_diff(a, "".join(changed), context)
                    self.assertEqual(_hunk_count(diff), 1 if gap == 2 * context else 2)

    def test_context_larger_than_the_text(self):
        self.assertEqual(
            unified_diff("a\nb\n", "a\nc\n", 100), "--- a\n+++ b\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n"
        )

    def test_deletions_come_before_insertions_in_a_hunk(self):
        diff = unified_diff("k\nx\ny\nk\n", "k\np\nq\nk\n", 0)
        self.assertEqual(diff, "--- a\n+++ b\n@@ -2,2 +2,2 @@\n-x\n-y\n+p\n+q\n")

    def test_carriage_return_is_part_of_its_line(self):
        # A lone "\r" does not end a line, so "a\rb\n" is one line, changed as a whole.
        self.assertEqual(
            unified_diff("a\rb\n", "a\rc\n"), "--- a\n+++ b\n@@ -1 +1 @@\n-a\rb\n+a\rc\n"
        )

    def test_unchanged_last_line_without_newline_gets_the_marker(self):
        diff = unified_diff("x\nend", "y\nend")
        self.assertEqual(
            diff, f"--- a\n+++ b\n@@ -1,2 +1,2 @@\n-x\n+y\n end\n{NO_NEWLINE}\n"
        )

    def test_every_output_line_ends_in_a_newline(self):
        rng = random.Random(9)
        for _ in range(100):
            a = "".join(rng.choice(["p\n", "q\n", "r"]) for _ in range(rng.randint(0, 6)))
            b = "".join(rng.choice(["p\n", "q\n", "r"]) for _ in range(rng.randint(0, 6)))
            diff = unified_diff(a, b, 1)
            with self.subTest(a=a, b=b):
                self.assertTrue(diff == "" or diff.endswith("\n"))
                for line in split_lines(diff)[2:]:
                    self.assertTrue(line.endswith("\n"))
                    self.assertIn(line[0], " -+@\\")

    def test_negative_context_is_rejected(self):
        with self.assertRaises(InvalidValueError) as caught:
            unified_diff("a\n", "b\n", -1)
        self.assertEqual(str(caught.exception), "context must be 0 or more, got -1")
        with self.assertRaises(InvalidValueError):
            unified_diff("a\n", "a\n", -1)  # checked even when the texts are equal

    def test_wrong_types_are_rejected(self):
        for args in ((b"a", "b"), ("a", None), ("a", "b", True), ("a", "b", 1.0)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    unified_diff(*args)


if __name__ == "__main__":
    unittest.main()
