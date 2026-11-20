"""Tests for textkit/diff/unified.py: ``unified_diff`` against GNU ``diff -u`` (plan task T3.6).

``GNU_CASES`` compares ``unified_diff`` byte for byte with the output of GNU-numbered
``diff -u``. Every case has a unique shortest edit, so any correct diff tool must print the
same hunks; the tie rule (tested in ``tests/test_diff_lcs.py``) never comes into play.
"""

import unittest

from textkit.diff import unified
from textkit.errors import InvalidValueError


def _lines(*items: object) -> str:
    """The text whose lines are ``items``, each followed by ``"\\n"``."""
    return "".join(f"{item}\n" for item in items)


# Captured once with `git diff --no-index --no-color -U<context> a b` (git 2.54.0, Apple
# Git-157), which numbers hunks like GNU diffutils (an empty range is the line before it:
# 0,0 at the top); this machine has no GNU diff, and the plan allows git as the capture tool.
# Only git's header lines (diff --git, index, --- a/<path>, +++ b/<path>) were replaced by
# "--- a" and "+++ b"; the hunks are pasted as git printed them. Each row is
# (what it pins, a, b, context, expected output).
GNU_CASES = [
    (
        "a gap of exactly 2 * context unchanged lines: one hunk",
        _lines(*range(1, 16)),
        _lines(1, 2, 30, *range(4, 10), 100, *range(11, 16)),
        3,
        "--- a\n+++ b\n@@ -1,13 +1,13 @@\n 1\n 2\n-3\n+30\n 4\n 5\n 6\n 7\n 8\n 9\n"
        "-10\n+100\n 11\n 12\n 13\n",
    ),
    (
        "a gap of 2 * context + 1 unchanged lines: two hunks",
        _lines(*range(1, 17)),
        _lines(1, 2, 30, *range(4, 11), 110, *range(12, 17)),
        3,
        "--- a\n+++ b\n@@ -1,6 +1,6 @@\n 1\n 2\n-3\n+30\n 4\n 5\n 6\n"
        "@@ -8,7 +8,7 @@\n 8\n 9\n 10\n-11\n+110\n 12\n 13\n 14\n",
    ),
    (
        "no final newline on either side, last line changed",
        "1\n2\n3\n4",
        "1\n2\n3\n40",
        3,
        "--- a\n+++ b\n@@ -1,4 +1,4 @@\n 1\n 2\n 3\n-4\n\\ No newline at end of file\n"
        "+40\n\\ No newline at end of file\n",
    ),
    (
        "no final newline on a context line",
        "1\n2\n3",
        "1\n20\n3",
        3,
        "--- a\n+++ b\n@@ -1,3 +1,3 @@\n 1\n-2\n+20\n 3\n\\ No newline at end of file\n",
    ),
    (
        "a final newline added",
        "1\n2",
        "1\n2\n",
        3,
        "--- a\n+++ b\n@@ -1,2 +1,2 @@\n 1\n-2\n\\ No newline at end of file\n+2\n",
    ),
    (
        "an insertion before line 1 at context 0",
        _lines(1, 2),
        _lines(0, 1, 2),
        0,
        "--- a\n+++ b\n@@ -0,0 +1 @@\n+0\n",
    ),
    (
        "a deletion of line 1 at context 0",
        _lines(1, 2),
        _lines(2),
        0,
        "--- a\n+++ b\n@@ -1 +0,0 @@\n-1\n",
    ),
    (
        "CRLF lines against LF lines: the \\r is part of the line",
        "1\r\n2\r\n",
        _lines(1, 2),
        3,
        "--- a\n+++ b\n@@ -1,2 +1,2 @@\n-1\r\n-2\r\n+1\n+2\n",
    ),
    (
        "an empty a",
        "",
        _lines(1, 2),
        3,
        "--- a\n+++ b\n@@ -0,0 +1,2 @@\n+1\n+2\n",
    ),
    (
        "an empty b",
        _lines(1, 2),
        "",
        3,
        "--- a\n+++ b\n@@ -1,2 +0,0 @@\n-1\n-2\n",
    ),
    (
        "a line appended: the context before it only",
        _lines(*range(1, 6)),
        _lines(*range(1, 7)),
        3,
        "--- a\n+++ b\n@@ -3,3 +3,4 @@\n 3\n 4\n 5\n+6\n",
    ),
    (
        "changes in the first and the last line at context 1: two hunks",
        _lines(*range(1, 9)),
        _lines(10, *range(2, 8), 80),
        1,
        "--- a\n+++ b\n@@ -1,2 +1,2 @@\n-1\n+10\n 2\n@@ -7,2 +7,2 @@\n 7\n-8\n+80\n",
    ),
]


class UnifiedDiffTest(unittest.TestCase):
    def test_matches_gnu_diff_byte_for_byte(self):
        for what, a, b, context, expected in GNU_CASES:
            with self.subTest(what):
                self.assertEqual(
                    unified.unified_diff(a, b, context).encode("utf-8"), expected.encode("utf-8")
                )

    def test_gnu_table_covers_the_required_cases(self):
        # The plan asks for at least 6 rows, these among them.
        outputs = [row[4] for row in GNU_CASES]
        self.assertGreaterEqual(len(GNU_CASES), 6)
        self.assertIn("--- a\n+++ b\n@@ -0,0 +1 @@\n+0\n", outputs)
        self.assertIn("--- a\n+++ b\n@@ -1 +0,0 @@\n-1\n", outputs)
        self.assertTrue(any(unified.NO_NEWLINE in out for out in outputs))
        hunk_counts = {(row[3], row[4].count("\n@@ ")) for row in GNU_CASES}
        self.assertIn((3, 1), hunk_counts)
        self.assertIn((3, 2), hunk_counts)

    def test_equal_texts_give_empty_string(self):
        for text in ("", "a\n", "a\nb", "x\r\n"):
            with self.subTest(text=text):
                self.assertEqual(unified.unified_diff(text, text), "")
                self.assertEqual(unified.unified_diff(text, text, context=0), "")

    def test_default_context_is_three(self):
        a = _lines(*range(1, 11))
        b = _lines(*range(1, 6), 60, *range(7, 11))
        self.assertEqual(unified.unified_diff(a, b), unified.unified_diff(a, b, 3))
        self.assertIn("@@ -3,7 +3,7 @@\n", unified.unified_diff(a, b))

    def test_context_is_clipped_to_the_text(self):
        a, b = _lines(1, 2, 3), _lines(1, 20, 3)
        expected = "--- a\n+++ b\n@@ -1,3 +1,3 @@\n 1\n-2\n+20\n 3\n"
        self.assertEqual(unified.unified_diff(a, b, 1), expected)
        self.assertEqual(unified.unified_diff(a, b, 1000), expected)
        self.assertEqual(unified.unified_diff(a, b, 0), "--- a\n+++ b\n@@ -2 +2 @@\n-2\n+20\n")

    def test_hunk_boundary_follows_two_times_context(self):
        # Two one-line changes with `gap` unchanged lines between them share a hunk exactly
        # when gap <= 2 * context, for several contexts.
        for context in range(0, 5):
            for gap in range(0, 2 * context + 3):
                a = _lines("x", *range(gap), "y")
                b = _lines("X", *range(gap), "Y")
                hunks = unified.unified_diff(a, b, context).count("\n@@ ")
                with self.subTest(context=context, gap=gap):
                    self.assertEqual(hunks, 1 if gap <= 2 * context else 2)

    def test_range_numbering(self):
        self.assertEqual(unified._range(0, 0), "0,0")
        self.assertEqual(unified._range(4, 0), "4,0")
        self.assertEqual(unified._range(0, 1), "1")
        self.assertEqual(unified._range(4, 1), "5")
        self.assertEqual(unified._range(4, 3), "5,3")

    def test_lone_carriage_return_and_form_feed_do_not_end_a_line(self):
        self.assertEqual(
            unified.unified_diff("a\rb\n", "a\rc\n"), "--- a\n+++ b\n@@ -1 +1 @@\n-a\rb\n+a\rc\n"
        )
        self.assertEqual(
            unified.unified_diff("a\x0cb\n", "a\x0cc\n"),
            "--- a\n+++ b\n@@ -1 +1 @@\n-a\x0cb\n+a\x0cc\n",
        )

    def test_deletions_come_before_insertions_in_a_hunk(self):
        out = unified.unified_diff(_lines(1, 2, 3), _lines(4, 5, 6))
        self.assertEqual(out, "--- a\n+++ b\n@@ -1,3 +1,3 @@\n-1\n-2\n-3\n+4\n+5\n+6\n")

    def test_every_output_line_ends_in_newline(self):
        out = unified.unified_diff("a", "b")
        self.assertEqual(
            out,
            "--- a\n+++ b\n@@ -1 +1 @@\n-a\n\\ No newline at end of file\n"
            "+b\n\\ No newline at end of file\n",
        )
        self.assertTrue(out.endswith("\n"))

    def test_negative_context_is_rejected(self):
        with self.assertRaises(InvalidValueError) as caught:
            unified.unified_diff("a\n", "b\n", -1)
        self.assertIn("-1", str(caught.exception))
        # Rejected even when the texts are equal: the argument is wrong either way.
        with self.assertRaises(InvalidValueError):
            unified.unified_diff("a\n", "a\n", context=-2)

    def test_wrong_types_raise_type_error(self):
        for args in ((b"a", "b"), ("a", None), ("a", "b", 1.5), ("a", "b", True), ("a", "b", "3")):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    unified.unified_diff(*args)


if __name__ == "__main__":
    unittest.main()
