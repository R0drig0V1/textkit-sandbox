"""Tests for textkit/diff/lcs.py, the longest common subsequence behind textkit.diff (T3.6).

``edit_script`` is private to the package (not in ``__all__``) but is tested directly: its
tie rule is stated in the ADR (``*-unified-diff-newlines-ties-and-cost.md``) and the hunks
of ``unified_diff`` and the pairs of ``diff_words`` follow from it. Minimality is checked
against a brute-force reference that shares no code with the module.
"""

import ast
import itertools
import pathlib
import random
import unittest

from textkit.diff.lcs import edit_script

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _rebuild(ops, a, b):
    """Replay ``ops``: return (kept + deleted items of a, kept + inserted items of b).

    Also checks that each step's (i, j) is the position before it, so the positions that
    unified.py turns into line numbers are tested on every script.
    """
    i = j = 0
    old, new = [], []
    for op, oi, oj in ops:
        assert (oi, oj) == (i, j), (op, oi, oj, i, j)
        if op in "=-":
            old.append(a[i])
            i += 1
        if op in "=+":
            new.append(b[j])
            j += 1
        if op == "=":
            assert a[oi] == b[oj]
    return old, new


def _brute_lcs_length(a, b):
    """Length of the longest common subsequence, by trying every subsequence of ``a``."""
    for size in range(min(len(a), len(b)), -1, -1):
        for picked in itertools.combinations(a, size):
            it = iter(b)
            if all(any(x == y for y in it) for x in picked):
                return size
    return 0


def _ops(script):
    """Only the op letters of a script, as a string ("=-+")."""
    return "".join(op for op, _, _ in script)


class EditScriptTest(unittest.TestCase):
    def test_equal_sequences_are_all_kept(self):
        a = ["x\n", "y\n", "z\n"]
        self.assertEqual(edit_script(a, list(a)), [("=", 0, 0), ("=", 1, 1), ("=", 2, 2)])

    def test_empty_sides(self):
        self.assertEqual(edit_script([], []), [])
        self.assertEqual(edit_script([], ["p", "q"]), [("+", 0, 0), ("+", 0, 1)])
        self.assertEqual(edit_script(["p", "q"], []), [("-", 0, 0), ("-", 1, 0)])

    def test_positions_replay_both_sequences(self):
        rng = random.Random(36)
        for _ in range(300):
            a = [rng.choice("abc") for _ in range(rng.randint(0, 9))]
            b = [rng.choice("abc") for _ in range(rng.randint(0, 9))]
            with self.subTest(a=a, b=b):
                self.assertEqual(_rebuild(edit_script(a, b), a, b), (a, b))

    def test_kept_items_are_a_longest_common_subsequence(self):
        rng = random.Random(3)
        for _ in range(200):
            a = [rng.choice("abcd") for _ in range(rng.randint(0, 7))]
            b = [rng.choice("abcd") for _ in range(rng.randint(0, 7))]
            with self.subTest(a=a, b=b):
                kept = _ops(edit_script(a, b)).count("=")
                self.assertEqual(kept, _brute_lcs_length(a, b))

    def test_replacement_deletes_before_inserting(self):
        self.assertEqual(
            edit_script(["k", "x", "y", "k"], ["k", "p", "q", "k"]),
            [("=", 0, 0), ("-", 1, 1), ("-", 2, 1), ("+", 3, 1), ("+", 3, 2), ("=", 3, 3)],
        )

    def test_every_run_of_changes_has_its_deletions_first(self):
        rng = random.Random(7)
        for _ in range(300):
            a = [rng.choice("abc") for _ in range(rng.randint(0, 9))]
            b = [rng.choice("abc") for _ in range(rng.randint(0, 9))]
            with self.subTest(a=a, b=b):
                for run in _ops(edit_script(a, b)).split("="):
                    self.assertNotIn("+-", run)

    def test_tie_keeps_the_earliest_match(self):
        # Rule 1: a[i] == b[j] is kept, so of two equal lines the first one stays.
        self.assertEqual(_ops(edit_script(["x", "x"], ["x"])), "=-")
        self.assertEqual(_ops(edit_script(["x"], ["x", "x"])), "=+")

    def test_tie_deletes_rather_than_inserts(self):
        # Rule 2: "p" then "q" and "q" then "p" have two LCS of length 1 ("p" or "q"); the
        # walk deletes a's "p" (keeping "q") instead of inserting b's "q" first.
        self.assertEqual(_ops(edit_script(["p", "q"], ["q", "p"])), "-=+")

    def test_common_prefix_and_suffix_are_kept(self):
        a = list("abcXdef")
        b = list("abcYYdef")
        self.assertEqual(_ops(edit_script(a, b)), "===-++===")

    def test_items_need_only_equality(self):
        # Any items compared with ==: tuples, ints and strings alike.
        self.assertEqual(_ops(edit_script([(1, 2), 3, "z"], [(1, 2), 4, "z"])), "=-+=")

    def test_no_difflib_in_textkit(self):
        # The plan forbids difflib in textkit/: the LCS is the package's own.
        for path in sorted((ROOT / "textkit").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                with self.subTest(path=path.name):
                    self.assertFalse([n for n in names if n.split(".")[0] == "difflib"])


if __name__ == "__main__":
    unittest.main()
