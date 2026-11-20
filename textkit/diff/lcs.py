"""Longest common subsequence and the edit script built from it (plan task T3.6).

``textkit.diff`` compares lines (``unified_diff``) and words (``diff_words``) with this module,
never with ``difflib``: the tie rule and the cost below are textkit's own and are decided in
the ADR ``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``.

Nothing here is in the package's ``__all__``, so every name is private to ``textkit.diff``
(phase 3 rule "Packages") even though it does not start with ``_``.
"""

from typing import List, Sequence, Tuple

# One step of an edit script: (op, i, j). ``op`` is "=" (a[i] and b[j] are kept), "-" (a[i]
# is deleted) or "+" (b[j] is inserted). (i, j) is always the position *before* the step:
# for "-", j is the number of items of b already produced; for "+", i is the number of items
# of a already consumed. unified.py reads its hunk line numbers straight from these.
Op = Tuple[str, int, int]


def edit_script(a: Sequence[object], b: Sequence[object]) -> List[Op]:
    """Return a shortest edit script that turns ``a`` into ``b``, keeping an LCS of both.

    Items are compared with ``==`` only. The script walks both sequences from the start; the
    kept items ("=" steps) form a longest common subsequence, so the number of "-" and "+"
    steps is the smallest possible. Ties between several longest subsequences are broken by
    one rule (the ADR states it):

    1. when ``a[i] == b[j]``, the two items are kept (the earliest possible match);
    2. otherwise ``a[i]`` is deleted when that still leaves an LCS of the same length, and
       ``b[j]`` is inserted only when deleting would lose one (deletions first);
    3. within a run of changes between two kept items, every "-" comes before every "+".

    Cost: the common prefix and suffix are matched in linear time; the rest takes
    ``O(n * m)`` time and memory, ``n`` and ``m`` being the lengths of the differing middle
    parts (one table cell per pair). It is meant for texts of up to a few thousand lines.

    Never raises for sequences; the caller checks the types of its own arguments.
    """
    n, m = len(a), len(b)
    # The common prefix and suffix are always part of an LCS (and rule 1 matches them first),
    # so only the middle needs the quadratic table. Most real diffs change a small part.
    prefix = 0
    while prefix < n and prefix < m and a[prefix] == b[prefix]:
        prefix += 1
    suffix = 0
    while suffix < n - prefix and suffix < m - prefix and a[n - 1 - suffix] == b[m - 1 - suffix]:
        suffix += 1

    ops: List[Op] = [("=", k, k) for k in range(prefix)]
    ops.extend(_middle(a[prefix : n - suffix], b[prefix : m - suffix], prefix, prefix))
    ops.extend(("=", n - suffix + k, m - suffix + k) for k in range(suffix))
    return ops


def _middle(a: Sequence[object], b: Sequence[object], i0: int, j0: int) -> List[Op]:
    """Edit script of the differing middle parts, positions shifted by ``(i0, j0)``."""
    n, m = len(a), len(b)
    # length[i][j] is the LCS length of a[i:] and b[j:]: a suffix table, so the walk below
    # can go forwards and decide each step from the start of the text.
    length = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, below = length[i], length[i + 1]
        item = a[i]
        for j in range(m - 1, -1, -1):
            if item == b[j]:
                row[j] = below[j + 1] + 1
            else:
                row[j] = below[j] if below[j] >= row[j + 1] else row[j + 1]

    steps: List[str] = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            steps.append("=")
            i += 1
            j += 1
        elif length[i + 1][j] >= length[i][j + 1]:
            steps.append("-")
            i += 1
        else:
            steps.append("+")
            j += 1
    steps.extend("-" * (n - i))
    steps.extend("+" * (m - j))
    return _positions(_deletions_first(steps), i0, j0)


def _deletions_first(steps: List[str]) -> List[str]:
    """Reorder each run of "-" and "+" steps so that its deletions come first (rule 3).

    Reordering inside a run keeps the same kept items, so the script stays a shortest one.
    """
    out: List[str] = []
    deleted = inserted = 0
    for step in steps + ["="]:  # a sentinel "=" flushes the last run
        if step == "-":
            deleted += 1
        elif step == "+":
            inserted += 1
        else:
            out.extend("-" * deleted)
            out.extend("+" * inserted)
            deleted = inserted = 0
            out.append(step)
    return out[:-1]  # drop the sentinel


def _positions(steps: List[str], i: int, j: int) -> List[Op]:
    """Attach to each step the position before it, starting at ``(i, j)``."""
    ops: List[Op] = []
    for step in steps:
        ops.append((step, i, j))
        if step != "+":
            i += 1
        if step != "-":
            j += 1
    return ops
