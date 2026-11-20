"""``unified_diff``: the unified format of GNU diffutils' ``diff -u`` (plan task T3.6).

The format, the line numbering and the hunk rule are described in ``docs/diff.md``; the
choices behind them (a text that does not end in a newline, the tie rule, the cost) are in
the ADR ``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``.
``split_lines`` is shared with ``patch.py``; it is not in ``__all__``, so it is private to
the package (phase 3 rule "Packages").
"""

from typing import List, Tuple

from textkit.diff.lcs import Op, edit_script
from textkit.errors import InvalidValueError

# The marker GNU diff prints after a line that has no newline at the end of the file.
NO_NEWLINE = "\\ No newline at end of file"

_PREFIX = {"=": " ", "-": "-", "+": "+"}


def split_lines(text: str) -> List[str]:
    """Split ``text`` after each ``"\\n"``, which stays at the end of its line.

    Only ``"\\n"`` ends a line, as in ``diff``: a ``"\\r"`` (so the ``"\\r"`` of ``"\\r\\n"``),
    ``"\\x0c"`` or ``"\\x85"`` is an ordinary character of its line, unlike
    ``str.splitlines``. The last line has no ``"\\n"`` when the text does not end in one;
    ``""`` has no lines. ``"".join(split_lines(text)) == text`` always holds.
    """
    parts = text.split("\n")
    lines = [part + "\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def unified_diff(a: str, b: str, context: int = 3) -> str:
    """Return the unified diff that turns text ``a`` into text ``b``, as GNU ``diff -u``.

    Lines are compared exactly (see ``split_lines``: a ``"\\r"`` is part of its line). The
    result starts with the headers ``--- a`` and ``+++ b``, then one hunk per group of
    changes: ``@@ -l,s +l,s @@`` followed by the lines, each prefixed with ``" "``
    (unchanged), ``"-"`` (only in ``a``) or ``"+"`` (only in ``b``), deletions before
    insertions. Each hunk shows up to ``context`` unchanged lines around its changes; two
    changes share a hunk when at most ``2 * context`` unchanged lines separate them. In a
    header, ``l`` is the first line of the range (from 1) and ``s`` its size; ``,s`` is left
    out when ``s == 1``, and an empty range is ``l,0`` with ``l`` the line before it (so
    ``-0,0`` at the top of a file: GNU numbering, not that of BSD ``diff``). A line that
    does not end in ``"\\n"`` (the last line of a text without a final newline) is followed
    by ``\\ No newline at end of file``. Every line of the result ends in ``"\\n"``.

    Returns ``""`` when ``a == b``. The lines are matched by a longest common subsequence
    (``lcs.edit_script``, no ``difflib``): ``O(n * m)`` time and memory in the sizes of the
    parts that differ, meant for texts of up to a few thousand lines.

    Raises:
        TypeError: if ``a`` or ``b`` is not a ``str``, or ``context`` is not an ``int``
            (``bool`` included).
        textkit.errors.InvalidValueError: if ``context < 0``, even when ``a == b``.
    """
    for name, value in (("a", a), ("b", b)):
        if not isinstance(value, str):
            raise TypeError(f"unified_diff() expects str for {name}, got {type(value).__name__}")
    if not isinstance(context, int) or isinstance(context, bool):
        raise TypeError(f"unified_diff() expects int for context, got {type(context).__name__}")
    if context < 0:
        raise InvalidValueError(f"context must be 0 or more, got {context}")
    if a == b:
        return ""

    old, new = split_lines(a), split_lines(b)
    ops = edit_script(old, new)
    out = ["--- a\n", "+++ b\n"]
    for start, stop in _hunks(ops, context):
        hunk = ops[start:stop]
        out.append(_header(hunk))
        for op, i, j in hunk:
            line = new[j] if op == "+" else old[i]
            out.append(_PREFIX[op] + line)
            if not line.endswith("\n"):
                out.append(f"\n{NO_NEWLINE}\n")
    return "".join(out)


def _hunks(ops: List[Op], context: int) -> List[Tuple[int, int]]:
    """Return the ``[start, stop)`` ranges of ``ops`` that form the hunks, in order.

    Two changes whose positions in ``ops`` are ``p < q`` (with only kept lines between them)
    are separated by ``q - p - 1`` unchanged lines; they share a hunk when that is at most
    ``2 * context``. Each range then extends ``context`` steps on both sides, clipped to
    the script; ranges never overlap, because a gap of more than ``2 * context`` leaves at
    least one unchanged line between the two ranges.
    """
    changes = [k for k, (op, _, _) in enumerate(ops) if op != "="]
    groups: List[List[int]] = []
    for k in changes:
        if groups and k - groups[-1][1] - 1 <= 2 * context:
            groups[-1][1] = k
        else:
            groups.append([k, k])
    return [(max(0, first - context), min(len(ops), last + 1 + context)) for first, last in groups]


def _header(hunk: List[Op]) -> str:
    """Return the ``@@ -l,s +l,s @@`` line of a hunk (GNU numbering)."""
    _, i, j = hunk[0]
    old_size = sum(op != "+" for op, _, _ in hunk)
    new_size = sum(op != "-" for op, _, _ in hunk)
    return f"@@ -{_range(i, old_size)} +{_range(j, new_size)} @@\n"


def _range(before: int, size: int) -> str:
    """Format one side of a hunk header from the number of lines ``before`` the range.

    A non-empty range starts at line ``before + 1``; an empty one is numbered by the line
    before it, ``before`` (0 at the top of the text), as GNU diff does.
    """
    if size == 0:
        return f"{before},0"
    if size == 1:
        return f"{before + 1}"
    return f"{before + 1},{size}"
