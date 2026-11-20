"""Tests for textkit/diff/patch.py: ``apply_patch`` and ``PatchError`` (plan task T3.6).

``ROUND_TRIP_CASES`` and 200 seeded random pairs check ``apply_patch(a, unified_diff(a, b))
== b``; ``APPLY_CASES`` pins hand-written patches (the empty patch, foreign headers, BSD
numbering) and the malformed ones, which must raise ``PatchError``.
"""

import random
import unittest

import textkit.diff
from textkit.errors import InvalidValueError
from textkit.diff import patch
from textkit.diff.unified import unified_diff

# (what it pins, a, b): apply_patch(a, unified_diff(a, b, context)) == b for every context.
ROUND_TRIP_CASES = [
    ("empty to empty", "", ""),
    ("empty to text", "", "a\nb\n"),
    ("text to empty", "a\nb\n", ""),
    ("one line changed", "a\n", "b\n"),
    ("no final newline on either side", "a\nb", "a\nc"),
    ("final newline removed", "a\nb\n", "a\nb"),
    ("final newline added", "a\nb", "a\nb\n"),
    ("change in the first line", "a\nb\nc\nd\ne\n", "A\nb\nc\nd\ne\n"),
    ("change in the last line", "a\nb\nc\nd\ne\n", "a\nb\nc\nd\nE\n"),
    ("two hunks", "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n", "0\n2\n3\n4\n5\n6\n7\n8\n9\n11\n"),
    ("two changes sharing a hunk", "1\n2\n3\n4\n5\n", "0\n2\n3\n4\n6\n"),
    ("CRLF lines to LF lines", "a\r\nb\r\n", "a\nb\n"),
]

HEADERS = "--- a\n+++ b\n"

# (what it pins, text, patch, the result or PatchError).
APPLY_CASES = [
    ("the empty patch returns the text", "a\nb\n", "", "a\nb\n"),
    ("the empty patch on an empty text", "", "", ""),
    ("headers with no hunk are malformed", "a\n", HEADERS, patch.PatchError),
    (
        "headers with file names and timestamps are ignored",
        "a\n",
        "--- old.txt\t2026-11-20 10:00:00.000000000 +0100\n"
        "+++ new.txt\t2026-11-20 10:05:00.000000000 +0100\n@@ -1 +1 @@\n-a\n+b\n",
        "b\n",
    ),
    ("git's a/ and b/ paths are ignored", "a\n", "--- a/x.txt\n+++ b/x.txt\n@@ -1 +1 @@\n-a\n+b\n", "b\n"),
    (
        "a section heading after the second @@ is ignored",
        "a\nb\n",
        HEADERS + "@@ -1,2 +1,2 @@ def f():\n a\n-b\n+c\n",
        "a\nc\n",
    ),
    ("a GNU insertion at the top: -0,0", "1\n", HEADERS + "@@ -0,0 +1 @@\n+0\n", "0\n1\n"),
    ("a BSD -1,0 hunk is applied after line 1", "1\n2\n", HEADERS + "@@ -1,0 +1 @@\n+0\n", "1\n0\n2\n"),
    ("a deletion of line 1 at context 0", "1\n2\n", HEADERS + "@@ -1 +0,0 @@\n-1\n", "2\n"),
    ("no headers is malformed", "a\n", "@@ -1 +1 @@\n-a\n+b\n", patch.PatchError),
    ("headers in the wrong order are malformed", "a\n", "+++ b\n--- a\n@@ -1 +1 @@\n-a\n+b\n", patch.PatchError),
    ("a second file is malformed", "a\n", HEADERS + "@@ -1 +1 @@\n-a\n+b\n" + HEADERS, patch.PatchError),
]


def _random_text(rng: random.Random) -> str:
    """A short text over a small alphabet of lines, one of them ending in "\\r\\n"; a third
    of the texts have a last line without a final newline."""
    lines = [rng.choice(["a\n", "b\n", "c\n", "a\r\n", "\n"]) for _ in range(rng.randint(0, 8))]
    if rng.random() < 1 / 3:
        lines.append(rng.choice(["a", "b", "z"]))
    return "".join(lines)


class ApplyPatchTest(unittest.TestCase):
    def test_round_trip_table(self):
        for what, a, b in ROUND_TRIP_CASES:
            for context in (0, 1, 3):
                with self.subTest(what, context=context):
                    self.assertEqual(patch.apply_patch(a, unified_diff(a, b, context)), b)

    def test_round_trip_on_random_pairs(self):
        rng = random.Random(20261120)
        for _ in range(200):
            a, b, context = _random_text(rng), _random_text(rng), rng.randint(0, 3)
            with self.subTest(a=a, b=b, context=context):
                self.assertEqual(patch.apply_patch(a, unified_diff(a, b, context)), b)

    def test_apply_table(self):
        for what, text, diff, expected in APPLY_CASES:
            with self.subTest(what):
                if expected is patch.PatchError:
                    with self.assertRaises(patch.PatchError):
                        patch.apply_patch(text, diff)
                else:
                    self.assertEqual(patch.apply_patch(text, diff), expected)

    def test_context_mismatch_names_the_hunk(self):
        diff = unified_diff("a\nb\nc\n", "a\nB\nc\n")
        with self.assertRaises(patch.PatchError) as caught:
            patch.apply_patch("a\nb\nX\n", diff)
        self.assertIn("@@ -1,3 +1,3 @@", str(caught.exception))
        self.assertIn("line 3", str(caught.exception))

    def test_removed_line_mismatch_names_the_hunk(self):
        diff = HEADERS + "@@ -2 +2 @@\n-b\n+B\n"
        with self.assertRaises(patch.PatchError) as caught:
            patch.apply_patch("a\nc\n", diff)
        self.assertIn("@@ -2 +2 @@", str(caught.exception))

    def test_no_fuzz_a_shifted_hunk_does_not_apply(self):
        # The hunk would apply one line further down; it is applied where it says or not at all.
        diff = unified_diff("a\nb\n", "a\nB\n", 0)
        self.assertEqual(diff, HEADERS + "@@ -2 +2 @@\n-b\n+B\n")
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("x\na\nb\n", diff)

    def test_carriage_return_must_match(self):
        diff = unified_diff("a\n", "b\n")
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a\r\n", diff)
        self.assertEqual(patch.apply_patch("a\r\n", unified_diff("a\r\n", "b\n")), "b\n")

    def test_missing_final_newline_must_match(self):
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a\n", unified_diff("a", "b"))
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a", unified_diff("a\n", "b\n"))

    def test_range_past_the_end_raises(self):
        with self.assertRaises(patch.PatchError) as caught:
            patch.apply_patch("a\n", HEADERS + "@@ -2 +2 @@\n-b\n+c\n")
        self.assertIn("@@ -2 +2 @@", str(caught.exception))

    def test_hunks_out_of_order_or_overlapping_raise(self):
        later = "@@ -3 +3 @@\n-c\n+C\n"
        earlier = "@@ -1 +1 @@\n-a\n+A\n"
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a\nb\nc\n", HEADERS + later + earlier)
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a\nb\n", HEADERS + "@@ -1,2 +1,2 @@\n a\n-b\n+B\n" + earlier)

    def test_malformed_hunks_raise(self):
        bad = {
            "not a hunk header": HEADERS + "@@ -1 +1\n-a\n+b\n",
            "a non-ASCII digit": HEADERS + "@@ -١ +1 @@\n-a\n+b\n",
            "fewer lines than stated": HEADERS + "@@ -1,2 +1,2 @@\n-a\n+b\n",
            "the next hunk starts too early": HEADERS + "@@ -1,2 +1 @@\n-a\n@@ -3 +2 @@\n-c\n",
            "more lines than stated": HEADERS + "@@ -1 +1 @@\n-a\n-b\n+c\n",
            "trailing lines after a hunk": HEADERS + "@@ -1 +1 @@\n-a\n+b\n+c\n",
            "an unknown prefix": HEADERS + "@@ -1,2 +1,2 @@\n a\n*b\n",
            "an empty line in a hunk": HEADERS + "@@ -1,2 +1,2 @@\n a\n\n",
            "a line without its newline": HEADERS + "@@ -1 +1 @@\n-a\n+b",
            "a non-empty range at line 0": HEADERS + "@@ -0 +1 @@\n-a\n+b\n",
            "two empty ranges": HEADERS + "@@ -1,0 +1,0 @@\n",
            "a marker first": HEADERS + "@@ -1 +1 @@\n\\ No newline at end of file\n-a\n+b\n",
            "two markers": HEADERS + "@@ -1 +1 @@\n-a\n\\ No newline\n\\ No newline\n+b\n",
            "a marker on an empty line": HEADERS + "@@ -0,0 +1 @@\n+\n\\ No newline\n",
            "a marked line that is not the last": HEADERS
            + "@@ -0,0 +1,2 @@\n+a\n\\ No newline\n+b\n",
        }
        for what, diff in bad.items():
            with self.subTest(what):
                with self.assertRaises(patch.PatchError):
                    patch.apply_patch("a\nb\nc\n", diff)

    def test_huge_header_numbers_raise_patch_error(self):
        # More than 4300 digits: int() raises a plain ValueError on Python 3.11+ (and the
        # 3.9.14+ security releases); it must come out as PatchError naming the hunk. On a
        # Python without the limit the number converts and the hunk fails to apply instead.
        nines = "9" * 5000
        for header in (f"@@ -{nines} +1 @@", f"@@ -1,{nines} +1 @@", f"@@ -1 +1,{nines} @@"):
            with self.subTest(header=header[:20]):
                with self.assertRaises(patch.PatchError) as caught:
                    patch.apply_patch("x\n", HEADERS + header + "\n-x\n+y\n")
                self.assertIs(type(caught.exception), patch.PatchError)
                self.assertIn(header, str(caught.exception))

    def test_unterminated_line_cannot_be_followed(self):
        # A hunk that ends the text without a newline, then a hunk that adds after it.
        diff = HEADERS + "@@ -1 +1 @@\n-a\n+a\n\\ No newline at end of file\n@@ -1,0 +2 @@\n+b\n"
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a\n", diff)
        # And a marked added line in the middle of the text.
        with self.assertRaises(patch.PatchError):
            patch.apply_patch("a\nb\n", HEADERS + "@@ -1 +1 @@\n-a\n+x\n\\ No newline\n")

    def test_patch_error_is_an_invalid_value_error_outside_all(self):
        self.assertTrue(issubclass(patch.PatchError, InvalidValueError))
        self.assertFalse(issubclass(patch.PatchError, ValueError))
        self.assertIs(textkit.diff.PatchError, patch.PatchError)
        self.assertNotIn("PatchError", textkit.diff.__all__)

    def test_wrong_types_raise_type_error(self):
        for args in ((b"a", ""), ("a", None), (None, None)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    patch.apply_patch(*args)


if __name__ == "__main__":
    unittest.main()
