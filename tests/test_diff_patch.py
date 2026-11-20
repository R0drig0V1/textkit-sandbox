"""Tests for textkit/diff/patch.py: ``apply_patch`` and ``PatchError`` (plan task T3.6).

Two tables: ``ROUND_TRIP_CASES`` checks ``apply_patch(a, unified_diff(a, b)) == b`` on the
cases the plan names; ``PATCH_CASES`` applies hand-written patches (the empty patch, headers
of other tools, headers with no hunk, BSD numbering) and gives the result or ``PatchError``.
"""

import random
import unittest

import textkit.diff
from textkit.diff import unified_diff
from textkit.errors import InvalidValueError, TextkitError
from textkit.diff.patch import PatchError, apply_patch

# (name, a, b): apply_patch(a, unified_diff(a, b, context)) must give b, for every context.
ROUND_TRIP_CASES = [
    ("empty text to text", "", "one\ntwo\n"),
    ("text to empty text", "one\ntwo\n", ""),
    ("one line", "one\n", "uno\n"),
    ("no final newline in a", "a\nb", "a\nb\n"),
    ("no final newline in b", "a\nb\n", "a\nb"),
    ("no final newline on either side", "a\nb", "a\nc"),
    ("change in the first line", "a\nb\nc\nd\n", "A\nb\nc\nd\n"),
    ("change in the last line", "a\nb\nc\nd\n", "a\nb\nc\nD\n"),
    ("two hunks", "".join(f"{k}\n" for k in range(20)),
     "".join(f"{k}\n" for k in range(20)).replace("\n2\n", "\ntwo\n").replace("17", "x")),
    ("two changes sharing a hunk", "a\nb\nc\nd\ne\nf\n", "a\nB\nc\nd\nE\nf\n"),
    ("CRLF lines", "a\r\nb\r\n", "a\r\nc\r\n"),
]

PATCH_ERROR = "PatchError"

# (name, text, patch, expected result or PATCH_ERROR)
PATCH_CASES = [
    ("empty patch returns the text", "a\nb", "", "a\nb"),
    ("empty patch on empty text", "", "", ""),
    ("headers with no hunk are malformed", "a\n", "--- a\n+++ b\n", PATCH_ERROR),
    ("headers of another tool are ignored", "a\nb\n",
     "--- a/x.txt\t2026-11-20 10:00:00.000000000 +0100\n+++ b/x.txt\t2026-11-20 10:01:00\n"
     "@@ -1,2 +1,2 @@\n a\n-b\n+c\n", "a\nc\n"),
    ("no headers at all", "a\nb\n", "@@ -2 +2 @@\n-b\n+c\n", "a\nc\n"),
    ("text after the @@ of a header (git) is ignored", "a\nb\n",
     "@@ -2 +2 @@ def f():\n-b\n+c\n", "a\nc\n"),
    ("BSD -1,0 is read as GNU: after line 1", "a\nb\n", "@@ -1,0 +1 @@\n+x\n", "a\nx\nb\n"),
    ("GNU -0,0 inserts at the top", "a\nb\n", "@@ -0,0 +1 @@\n+x\n", "x\na\nb\n"),
    ("a line differs", "a\nb\n", "@@ -2 +2 @@\n-z\n+c\n", PATCH_ERROR),
    ("garbage", "a\n", "hello\n", PATCH_ERROR),
]


class ApplyPatchTest(unittest.TestCase):
    def test_round_trip_table(self):
        for name, a, b in ROUND_TRIP_CASES:
            for context in (0, 1, 3):
                with self.subTest(name, context=context):
                    self.assertEqual(apply_patch(a, unified_diff(a, b, context)), b)

    def test_round_trip_on_200_random_pairs(self):
        rng = random.Random(2026)
        alphabet = ["a\n", "b\n", "c\n", "a\r\n", "\n"]

        def text():
            lines = [rng.choice(alphabet) for _ in range(rng.randint(0, 10))]
            if rng.random() < 0.3:  # a text without a final newline
                lines.append(rng.choice(["a", "b", "z", "\r"]))
            return "".join(lines)

        for _ in range(200):
            a, b, context = text(), text(), rng.randint(0, 3)
            with self.subTest(a=a, b=b, context=context):
                self.assertEqual(apply_patch(a, unified_diff(a, b, context)), b)

    def test_patch_case_table(self):
        for name, text, patch, expected in PATCH_CASES:
            with self.subTest(name):
                if expected == PATCH_ERROR:
                    with self.assertRaises(PatchError):
                        apply_patch(text, patch)
                else:
                    self.assertEqual(apply_patch(text, patch), expected)

    def test_hunks_apply_at_their_stated_lines_only(self):
        # No fuzz: the hunk's lines exist in the text, but one line lower than stated.
        patch = "@@ -1,2 +1,2 @@\n a\n-b\n+c\n"
        with self.assertRaises(PatchError):
            apply_patch("z\na\nb\n", patch)
        self.assertEqual(apply_patch("a\nb\nz\n", patch), "a\nc\nz\n")

    def test_line_endings_must_match_exactly(self):
        with self.assertRaises(PatchError):
            apply_patch("a\r\n", "@@ -1 +1 @@\n-a\n+b\n")
        with self.assertRaises(PatchError):  # the marker says "a" has no newline; it has one
            apply_patch("a\n", "@@ -1 +1 @@\n-a\n\\ No newline at end of file\n+b\n")

    def test_applies_several_hunks_in_order(self):
        text = "".join(f"{k}\n" for k in range(1, 11))
        patch = "@@ -1 +1 @@\n-1\n+one\n@@ -5,0 +6 @@\n+5.5\n@@ -10 +11 @@\n-10\n+ten\n"
        self.assertEqual(
            apply_patch(text, patch), "one\n2\n3\n4\n5\n5.5\n6\n7\n8\n9\nten\n"
        )

    def test_exported_from_the_package(self):
        self.assertIs(textkit.diff.apply_patch, apply_patch)
        self.assertIs(textkit.diff.PatchError, PatchError)
        self.assertEqual(textkit.diff.__all__, sorted(textkit.diff.__all__))
        self.assertNotIn("PatchError", textkit.diff.__all__)

    def test_wrong_types_are_rejected(self):
        for args in ((b"a\n", ""), ("a\n", None), (None, "")):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    apply_patch(*args)


class PatchErrorTest(unittest.TestCase):
    def assertPatchError(self, text, patch, *fragments):
        with self.assertRaises(PatchError) as caught:
            apply_patch(text, patch)
        for fragment in fragments:
            self.assertIn(fragment, str(caught.exception))

    def test_base_class_is_invalid_value_error(self):
        # Phase 3 rule "Errors": since T3.2, a tool's errors subclass InvalidValueError,
        # which is a TextkitError and not a ValueError.
        self.assertTrue(issubclass(PatchError, InvalidValueError))
        self.assertTrue(issubclass(PatchError, TextkitError))
        self.assertFalse(issubclass(PatchError, ValueError))

    def test_context_mismatch_names_the_hunk(self):
        self.assertPatchError("a\nb\nc\n", "@@ -1,3 +1,3 @@\n a\n-b\n+B\n x\n",
                              "@@ -1,3 +1,3 @@", "line 3", "'x\\n'", "'c\\n'")

    def test_removed_line_mismatch_names_the_hunk(self):
        self.assertPatchError("a\nb\n", "--- a\n+++ b\n@@ -2 +2 @@\n-q\n+r\n",
                              "@@ -2 +2 @@", "line 2")

    def test_hunk_past_the_end_of_the_text(self):
        self.assertPatchError("a\n", "@@ -2 +2 @@\n-b\n+c\n", "@@ -2 +2 @@", "1 lines")

    def test_hunks_out_of_order_or_overlapping(self):
        text = "a\nb\nc\n"
        self.assertPatchError(text, "@@ -3 +3 @@\n-c\n+C\n@@ -1 +1 @@\n-a\n+A\n",
                              "@@ -1 +1 @@", "previous hunk")
        self.assertPatchError(text, "@@ -1,2 +1,2 @@\n a\n-b\n+B\n@@ -2 +2 @@\n-b\n+X\n",
                              "@@ -2 +2 @@", "previous hunk")

    def test_malformed_hunks(self):
        cases = [
            ("a '---' header alone", "--- a\n@@ -1 +1 @@\n-a\n+b\n", "'+++ '"),
            ("a bad @@ line", "@@ -x +1 @@\n-a\n+b\n", "hunk header"),
            ("fewer lines than counted", "@@ -1,2 +1,2 @@\n-a\n+b\n", "@@ -1,2 +1,2 @@"),
            ("more lines than counted", "@@ -1 +1 @@\n-a\n+b\n+c\n", "@@ -1 +1 @@"),
            ("a stray line after a complete hunk", "@@ -1 +1 @@\n-a\n+b\nhello\n",
             "@@ -1 +1 @@"),
            ("non-ASCII digits in the header", "@@ -\u0661 +1 @@\n-a\n+b\n",
             "hunk header"),
            ("more removed lines than counted", "@@ -1 +1,2 @@\n-a\n-b\n+c\n+d\n",
             "more lines than its header counts"),
            ("an unknown line tag", "@@ -1 +1 @@\n*a\n+b\n", "@@ -1 +1 @@"),
            ("an empty line inside a hunk", "@@ -1,2 +1,2 @@\n a\n\n", "@@ -1,2 +1,2 @@"),
            ("a marker right after the header", "@@ -1 +1 @@\n\\ No newline\n-a\n+b\n",
             "@@ -1 +1 @@"),
            ("a line after the marker on its side",
             "@@ -1,2 +1 @@\n-a\n\\ No newline at end of file\n-b\n+c\n", "same side"),
            ("line 0 with lines", "@@ -0,1 +1 @@\n-a\n+b\n", "line 0"),
            ("a hunk with no lines", "@@ -1,0 +1,0 @@\n", "no lines"),
            ("a last line without newline", "@@ -1 +1 @@\n-a\n+b", "newline"),
        ]
        for name, patch, fragment in cases:
            with self.subTest(name):
                self.assertPatchError("a\n", patch, fragment)

    def test_lines_glued_by_a_missing_newline_are_rejected(self):
        # After a last line with no newline, nothing can be added...
        self.assertPatchError("a", "@@ -1,0 +2 @@\n+b\n", "@@ -1,0 +2 @@", "no newline")
        # ...and a hunk whose new side ends without a newline must reach the end of the text.
        self.assertPatchError("a\nb\n", "@@ -1 +1 @@\n-a\n+x\n\\ No newline at end of file\n",
                              "@@ -1 +1 @@", "not at the end")

    def test_header_numbers_are_ascii_digits_only(self):
        # "\u0663" is ARABIC-INDIC DIGIT THREE: re's \d and int() accept it, the format not.
        patch = "@@ -\u0663 +1 @@\n-c\n+z\n"
        self.assertPatchError("a\nb\nc\n", patch, "patch line 1", "hunk header", "\u0663")

    def test_a_line_past_a_complete_hunk_names_that_hunk(self):
        self.assertPatchError("a\nb\nc\n", "@@ -1 +1 @@\n-a\n+x\n+y\n",
                              "hunk @@ -1 +1 @@", "patch line 4",
                              "more lines than its header counts", "'+y'")
        self.assertPatchError("a\nb\n", "@@ -1 +1 @@\n-a\n+x\n@@ -2 +2 @@\n-b\n+y\n z\n",
                              "hunk @@ -2 +2 @@", "patch line 7")

    def test_huge_numbers_do_not_leak_a_plain_value_error(self):
        # int() refuses more than 4300 digits on Python 3.11+; the standard library's
        # ValueError must not escape (phase 3 rule "Errors"). On 3.9 the number parses and
        # the hunk is past the end.
        self.assertPatchError("a\n", f"@@ -{'9' * 5000} +1 @@\n-a\n+b\n", "@@ -999")


if __name__ == "__main__":
    unittest.main()
