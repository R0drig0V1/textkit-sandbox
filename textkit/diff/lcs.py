"""Longest common subsequence and edit script, the engine of ``textkit.diff`` (plan task T3.6).

``edit_script(a, b)`` turns one sequence into another with the fewest deletions and
insertions, keeping a longest common subsequence (LCS) unchanged. ``split_lines`` cuts a text
into the lines that ``unified_diff`` and ``apply_patch`` work on. Both are private to the
package (only the names in ``textkit/diff/__init__.py``'s ``__all__`` are public), so they
have no README row.

The choices made here (the tie rule, the cost) are decided in the ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``; change that ADR first.
"""

from typing import Hashable, List, Sequence, Tuple, TypeVar

T = TypeVar("T", bound=Hashable)

# The three operations of an edit script: keep an item of both sequences, delete an item of
# the first, insert an item of the second. The strings are the ones diff_words returns.
EQUAL = "="
DELETE = "-"
INSERT = "+"


def split_lines(text: str) -> List[str]:
    """Split ``text`` after each ``"\\n"``, which stays at the end of its line.

    Only ``"\\n"`` ends a line, as in GNU ``diff``: a ``"\\r"`` is an ordinary character of
    its line, so ``"a\\r\\n"`` and ``"a\\n"`` are different lines. The last line has no
    ``"\\n"`` when the text does not end in one. ``""`` has no lines. Unlike
    ``str.splitlines``, ``"\\x0c"``, ``"\\x85"`` and the other Unicode line breaks do not end
    a line, and ``"".join(split_lines(text)) == text`` always holds.
    """
    lines = text.split("\n")
    # split() leaves "" after a final "\n" (or for ""), which is not a line.
    tail = lines.pop()
    result = [line + "\n" for line in lines]
    if tail:
        result.append(tail)
    return result


def edit_script(a: Sequence[T], b: Sequence[T]) -> List[Tuple[str, T]]:
    """Return a shortest edit script from ``a`` to ``b`` as ``(op, item)`` pairs.

    ``op`` is ``EQUAL`` (the item is in both, taken from ``a``), ``DELETE`` (from ``a``) or
    ``INSERT`` (from ``b``). Reading the ``EQUAL`` and ``DELETE`` items gives ``a``; reading
    the ``EQUAL`` and ``INSERT`` items gives ``b``; the ``EQUAL`` items are a longest common
    subsequence. Items are compared with ``==`` and must be hashable.

    When several longest common subsequences exist, the tie rule of the ADR picks one:

    1. Items common to the start of both sequences, then items common to their end, are
       kept unchanged (this is never worse, and it is what GNU ``diff`` does).
    2. Between them, a walk from the top keeps a pair of equal items as soon as it meets one
       (the earliest match); otherwise it deletes the item of ``a`` when that still allows a
       longest common subsequence, and inserts the item of ``b`` only when it does not.

    Rule 2 also makes every run of changes list its deletions before its insertions: after
    an insertion, the current item of ``a`` is part of every remaining LCS, so the next
    step that is not an insertion keeps it.

    Cost: the common start and end take O(n + m); the rest takes O(n' * m') time and memory,
    where ``n'`` and ``m'`` are the lengths left between them (a table of LCS lengths). That
    suits texts of up to a few thousand lines; the ADR has the numbers.
    """
    n, m = len(a), len(b)
    start = 0
    while start < n and start < m and a[start] == b[start]:
        start += 1
    end_a, end_b = n, m
    while end_a > start and end_b > start and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1

    script: List[Tuple[str, T]] = [(EQUAL, item) for item in a[:start]]
    script += _middle(a[start:end_a], b[start:end_b])
    script += [(EQUAL, item) for item in a[end_a:]]
    return script


def _middle(a: Sequence[T], b: Sequence[T]) -> List[Tuple[str, T]]:
    """The edit script of the part between the common start and end (rule 2 of the ADR)."""
    n, m = len(a), len(b)
    if not n or not m:
        return [(DELETE, item) for item in a] + [(INSERT, item) for item in b]
    # Compare small integers instead of the items themselves: lines can be long, and the
    # table compares every pair once.
    ids: dict = {}
    xa = [ids.setdefault(item, len(ids)) for item in a]
    xb = [ids.setdefault(item, len(ids)) for item in b]
    # table[i][j] is the LCS length of a[i:] and b[j:]; row n and column m are 0. Suffix
    # lengths (not prefix ones) let the walk below go forwards, from the top of the texts.
    table = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, below, ai = table[i], table[i + 1], xa[i]
        for j in range(m - 1, -1, -1):
            if ai == xb[j]:
                row[j] = below[j + 1] + 1
            else:
                right, down = row[j + 1], below[j]
                row[j] = right if right > down else down
    script: List[Tuple[str, T]] = []
    i = j = 0
    while i < n and j < m:
        if xa[i] == xb[j]:
            # Keeping a pair of equal items is always part of some LCS: the earliest match.
            script.append((EQUAL, a[i]))
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            # Deleting a[i] loses nothing: deletions win ties.
            script.append((DELETE, a[i]))
            i += 1
        else:
            script.append((INSERT, b[j]))
            j += 1
    script += [(DELETE, item) for item in a[i:]]
    script += [(INSERT, item) for item in b[j:]]
    return script
