"""``unified_diff``: the unified format of GNU ``diff -u`` (plan task T3.6).

The lines come from ``lcs.split_lines`` (a line ends after each ``"\\n"``) and the changes
from ``lcs.edit_script`` (its own LCS, never ``difflib``). The format, the numbering of empty
ranges and the ``\\ No newline at end of file`` marker follow GNU diffutils, not the
Apple/FreeBSD ``diff`` of macOS; ``docs/diff.md`` describes it and the ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md`` explains the choices.
"""

from typing import List, Tuple

from textkit.diff.lcs import DELETE, EQUAL, INSERT, edit_script, split_lines

# Printed after a line that does not end in "\n" (the last line of a text without a final
# newline), exactly as GNU diff prints it in the C locale.
NO_NEWLINE = "\\ No newline at end of file\n"

# The prefix of each line of a hunk, by edit operation.
_PREFIX = {EQUAL: " ", DELETE: "-", INSERT: "+"}


def unified_diff(a: str, b: str, context: int = 3) -> str:
    """Return the differences from ``a`` to ``b`` in the unified format of GNU ``diff -u``.

    Lines end after each ``"\\n"``, which belongs to its line; a ``"\\r"`` is part of the
    line (``"x\\r\\n"`` and ``"x\\n"`` differ). The result starts with the headers
    ``"--- a\\n+++ b\\n"``, followed by one hunk per group of changes::

        @@ -l,s +l,s @@
         context line
        -line of a
        +line of b

    ``l`` is the first line of the range (from 1) and ``s`` its length; ``,s`` is left out
    when ``s == 1``, and an empty range is ``l,0`` with ``l`` the line before it (``0,0`` at
    the top of a text), as GNU diffutils numbers it. Each hunk has up to ``context``
    unchanged lines before and after its changes; two changes share a hunk when at most
    ``2 * context`` unchanged lines separate them. A line that does not end in ``"\\n"`` is
    followed by ``\\ No newline at end of file``. In a run of changes the removed lines come
    before the added ones; when several shortest diffs exist, the tie rule of the ADR picks
    one. Returns ``""`` when ``a == b``.

    Cost: O(n' * m') time and memory for the n' and m' lines left after removing the common
    first and last lines; meant for texts of up to a few thousand lines (see the ADR).

    Raises:
        TypeError: if ``a`` or ``b`` is not a ``str``, or ``context`` is not an ``int``.
        ValueError: if ``context`` is negative.
    """
    for name, value in (("a", a), ("b", b)):
        if not isinstance(value, str):
            raise TypeError(f"unified_diff() expects str for {name}, got {type(value).__name__}")
    # bool is an int subclass, but True as a context is a mistake, not a count.
    if not isinstance(context, int) or isinstance(context, bool):
        raise TypeError(f"unified_diff() expects int for context, got {type(context).__name__}")
    if context < 0:
        raise ValueError(f"context must be 0 or more, got {context}")
    if a == b:
        return ""
    script = edit_script(split_lines(a), split_lines(b))
    # old_at[k] and new_at[k]: lines of a and of b before script[k], for the hunk headers.
    old_at, new_at = [0], [0]
    for op, _ in script:
        old_at.append(old_at[-1] + (op != INSERT))
        new_at.append(new_at[-1] + (op != DELETE))
    out = ["--- a\n", "+++ b\n"]
    for lo, hi in _hunks(script, context):
        old = _range(old_at[lo], old_at[hi] - old_at[lo])
        new = _range(new_at[lo], new_at[hi] - new_at[lo])
        out.append(f"@@ -{old} +{new} @@\n")
        for op, line in script[lo:hi]:
            out.append(_PREFIX[op] + line)
            if not line.endswith("\n"):
                out.append("\n" + NO_NEWLINE)
    return "".join(out)


def _hunks(script: List[Tuple[str, str]], context: int) -> List[Tuple[int, int]]:
    """Group the changes of ``script`` into hunks; return each as a slice ``(lo, hi)``.

    A change joins the current hunk when at most ``2 * context`` unchanged entries separate
    it from the previous change (the context after one and before the other would touch or
    overlap); otherwise it starts a new hunk. Each slice extends ``context`` entries beyond
    its first and last change, clipped to the script.
    """
    changes = [k for k, (op, _) in enumerate(script) if op != EQUAL]
    groups: List[List[int]] = []
    for k in changes:
        if groups and k - groups[-1][1] - 1 <= 2 * context:
            groups[-1][1] = k
        else:
            groups.append([k, k])
    return [(max(0, first - context), min(len(script), last + 1 + context)) for first, last in groups]


def _range(skipped: int, size: int) -> str:
    """Format a range of ``size`` lines after the first ``skipped`` lines of a text.

    A non-empty range starts at line ``skipped + 1``; an empty one is numbered after the
    line before it, ``skipped`` (GNU diffutils; BSD diff would write ``skipped + 1``).
    """
    if size == 0:
        return f"{skipped},0"
    if size == 1:
        return f"{skipped + 1}"
    return f"{skipped + 1},{size}"
