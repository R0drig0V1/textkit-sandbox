"""Tests for textkit/diff/lcs.py: line splitting and the edit script (plan task T3.6).

The tie rule tested here is the one of the ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``. Optimality is checked against an
independent LCS length (``_lcs_length``, a plain recursion), not against the module itself.
"""

import functools
import random
import unittest
from typing import List, Sequence, Tuple

from textkit.diff import lcs

D, E, I = lcs.DELETE, lcs.EQUAL, lcs.INSERT


def _lcs_length(a: Sequence[object], b: Sequence[object]) -> int:
    """The length of a longest common subsequence, by the textbook recursion."""

    @functools.lru_cache(maxsize=None)
    def length(i: int, j: int) -> int:
        if i == len(a) or j == len(b):
            return 0
        if a[i] == b[j]:
            return 1 + length(i + 1, j + 1)
        return max(length(i + 1, j), length(i, j + 1))

    return length(0, 0)


def _sides(script: List[Tuple[str, object]]) -> Tuple[list, list]:
    """The two sequences an edit script describes: (EQUAL + DELETE, EQUAL + INSERT)."""
    return (
        [item for op, item in script if op != I],
        [item for op, item in script if op != D],
    )


def _random_sequences(rng: random.Random) -> Tuple[List[str], List[str]]:
    """Two short sequences over a three-letter alphabet, so they share many items."""
    return (
        [rng.choice("abc") for _ in range(rng.randint(0, 9))],
        [rng.choice("abc") for _ in range(rng.randint(0, 9))],
    )


class SplitLinesTest(unittest.TestCase):
    def test_newline_stays_in_its_line(self):
        self.assertEqual(lcs.split_lines("a\nb\n"), ["a\n", "b\n"])

    def test_last_line_without_newline(self):
        self.assertEqual(lcs.split_lines("a\nb"), ["a\n", "b"])

    def test_empty_text_and_blank_lines(self):
        self.assertEqual(lcs.split_lines(""), [])
        self.assertEqual(lcs.split_lines("\n"), ["\n"])
        self.assertEqual(lcs.split_lines("\n\n"), ["\n", "\n"])

    def test_only_newline_ends_a_line(self):
        # Unlike str.splitlines: "\r" (alone or before "\n"), form feed, NEL and the Unicode
        # line separator are characters of their line.
        self.assertEqual(lcs.split_lines("a\r\nb\rc\n"), ["a\r\n", "b\rc\n"])
        self.assertEqual(lcs.split_lines("a\x0cb\x85c d"), ["a\x0cb\x85c d"])

    def test_join_gives_the_text_back(self):
        rng = random.Random(6)
        for _ in range(100):
            text = "".join(rng.choice(["a", "\n", "\r", "\r\n", "é", " "]) for _ in range(12))
            with self.subTest(text=text):
                self.assertEqual("".join(lcs.split_lines(text)), text)


class EditScriptTest(unittest.TestCase):
    def test_identical_sequences_are_all_equal(self):
        self.assertEqual(lcs.edit_script("abc", "abc"), [(E, "a"), (E, "b"), (E, "c")])

    def test_empty_sides(self):
        self.assertEqual(lcs.edit_script("", ""), [])
        self.assertEqual(lcs.edit_script("ab", ""), [(D, "a"), (D, "b")])
        self.assertEqual(lcs.edit_script("", "ab"), [(I, "a"), (I, "b")])

    def test_script_describes_both_sequences(self):
        rng = random.Random(1)
        for _ in range(200):
            a, b = _random_sequences(rng)
            with self.subTest(a=a, b=b):
                self.assertEqual(_sides(lcs.edit_script(a, b)), (a, b))

    def test_equal_items_are_a_longest_common_subsequence(self):
        rng = random.Random(2)
        for _ in range(200):
            a, b = _random_sequences(rng)
            with self.subTest(a=a, b=b):
                kept = [item for op, item in lcs.edit_script(a, b) if op == E]
                self.assertEqual(len(kept), _lcs_length(a, b))

    def test_replacement_deletes_before_inserting(self):
        self.assertEqual(lcs.edit_script("axb", "ayb"), [(E, "a"), (D, "x"), (I, "y"), (E, "b")])

    def test_tie_is_won_by_the_deletion(self):
        # "ab" -> "ba": keeping "a" or keeping "b" are both shortest. Deleting "a" first
        # keeps "b" (rule 2 of the ADR).
        self.assertEqual(lcs.edit_script("ab", "ba"), [(D, "a"), (E, "b"), (I, "a")])

    def test_earliest_match_is_kept(self):
        # The "x" of a could pair with either "x" of b; the walk pairs it with the first.
        self.assertEqual(
            lcs.edit_script("pxq", "xrx"),
            [(D, "p"), (E, "x"), (D, "q"), (I, "r"), (I, "x")],
        )

    def test_common_start_is_kept_before_common_end(self):
        # "x" is both the first and the last item of a; the common start wins (rule 1).
        self.assertEqual(lcs.edit_script("xyx", "x"), [(E, "x"), (D, "y"), (D, "x")])
        self.assertEqual(lcs.edit_script("yx", "x"), [(D, "y"), (E, "x")])

    def test_no_run_of_changes_inserts_before_deleting(self):
        rng = random.Random(3)
        for _ in range(300):
            a, b = _random_sequences(rng)
            ops = "".join(op for op, _ in lcs.edit_script(a, b))
            with self.subTest(a=a, b=b):
                self.assertNotIn(I + D, ops)

    def test_items_need_only_be_hashable(self):
        a = [("x", 1), ("y", 2)]
        b = [("y", 2), ("z", 3)]
        self.assertEqual(lcs.edit_script(a, b), [(D, ("x", 1)), (E, ("y", 2)), (I, ("z", 3))])


if __name__ == "__main__":
    unittest.main()
