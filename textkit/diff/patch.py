"""``apply_patch`` and ``PatchError``: apply a unified diff to a text (plan task T3.6).

The patch format is the one ``unified_diff`` writes, with GNU numbering (``docs/diff.md``);
the reading rules are strict on purpose: a hunk applies at the lines its header states or
not at all (no fuzz, no offset search), so a patch that does not fit raises instead of
changing the wrong lines. ``PatchError`` is importable from ``textkit.diff`` but not in its
``__all__``, which lists functions only (phase 3 rule "Packages").
"""

import re
from typing import List, NamedTuple, Optional, Tuple

from textkit.diff.unified import split_lines
from textkit.errors import InvalidValueError


class PatchError(InvalidValueError):
    """A patch is not a well-formed unified diff, or does not match the text it is applied to.

    It subclasses ``textkit.errors.InvalidValueError`` (phase 3 rule "Errors"), so it is a
    ``TextkitError`` and not a ``ValueError``. When the problem is in one hunk, the message
    contains that hunk's ``@@`` header.
    """


# "@@ -l[,s] +l[,s] @@", optionally followed by a space and any text (git writes the
# enclosing function there). The line's "\n" is removed before matching. The numbers are
# ASCII digits only: "\d" would also accept "\u0663" (ARABIC-INDIC DIGIT THREE), which int()
# reads as 3, so a header no diff tool writes would apply.
_HUNK_HEADER = re.compile(r"@@ -([0-9]+)(?:,([0-9]+))? \+([0-9]+)(?:,([0-9]+))? @@(?: .*)?")


class _Hunk(NamedTuple):
    """One parsed hunk: its header line, old range and the lines of both sides."""

    header: str
    old_start: int
    old_size: int
    old_lines: List[str]
    new_lines: List[str]


def apply_patch(text: str, patch: str) -> str:
    """Return ``text`` with the unified diff ``patch`` applied.

    ``apply_patch(a, unified_diff(a, b)) == b`` for any texts ``a`` and ``b``. The patch is
    read with GNU numbering: a hunk ``-l,s`` with ``s > 0`` replaces lines ``l`` to
    ``l + s - 1``; with ``s == 0`` it inserts after line ``l`` (0: at the top). So a BSD
    ``diff`` hunk ``-1,0``, meant as "at the top", is applied after line 1. Each hunk applies
    exactly at its stated lines (no fuzz): every context (``" "``) and removed (``"-"``)
    line must equal the text's line there, ``"\\r"`` and the final newline included. The
    ``+l`` start of a header is not checked; the sizes are, against the hunk's lines.

    The patch is optional ``--- `` and ``+++ `` header lines (followed by anything: a file
    name, a timestamp, ``a/`` paths; ignored) and then one or more hunks in text order. A
    ``\\`` line (``\\ No newline at end of file``) after a hunk line removes that line's
    final ``"\\n"``. ``""`` is the empty patch and returns ``text`` unchanged.

    Raises:
        TypeError: if ``text`` or ``patch`` is not a ``str``.
        PatchError: (a ``textkit.errors.InvalidValueError``) if ``patch`` is not a
            well-formed unified diff (no hunk after the
            headers, a bad ``@@`` line or one with non-ASCII digits, a hunk whose lines do
            not add up to its header, a last line without ``"\\n"``, ...), or a hunk does
            not match ``text`` (a line
            differs, the hunk goes past the end of the text or overlaps the previous one);
            the message contains the hunk's ``@@`` header when one hunk is at fault.
    """
    for name, value in (("text", text), ("patch", patch)):
        if not isinstance(value, str):
            raise TypeError(f"apply_patch() expects str for {name}, got {type(value).__name__}")
    if patch == "":
        return text

    lines = split_lines(text)
    out: List[str] = []
    cursor = 0  # lines[:cursor] are already in out (copied or replaced)
    for hunk in _parse(patch):
        start = hunk.old_start if hunk.old_size == 0 else hunk.old_start - 1
        stop = start + hunk.old_size
        if start < cursor:
            raise PatchError(f"hunk {hunk.header} overlaps or comes before the previous hunk")
        if stop > len(lines):
            raise PatchError(
                f"hunk {hunk.header} goes past the end of the text ({len(lines)} lines)"
            )
        for offset, (expected, found) in enumerate(zip(hunk.old_lines, lines[start:stop])):
            if expected != found:
                raise PatchError(
                    f"hunk {hunk.header} does not match line {start + offset + 1}: "
                    f"expected {expected!r}, found {found!r}"
                )
        out.extend(lines[cursor:start])
        if hunk.new_lines:
            # Only the text's last line can lack a newline; adding lines after it would glue
            # the first of them onto it, which no diff of two texts asks for.
            if out and not out[-1].endswith("\n"):
                raise PatchError(
                    f"hunk {hunk.header} adds lines after a line with no newline at its end"
                )
            if not hunk.new_lines[-1].endswith("\n") and stop < len(lines):
                raise PatchError(
                    f"hunk {hunk.header} ends without a newline but is not at the end of the text"
                )
        out.extend(hunk.new_lines)
        cursor = stop
    out.extend(lines[cursor:])
    return "".join(out)


def _parse(patch: str) -> List[_Hunk]:
    """Parse a non-empty patch into its hunks; raise ``PatchError`` if it is malformed."""
    lines = split_lines(patch)
    if not lines[-1].endswith("\n"):
        raise PatchError(f"patch line {len(lines)} does not end with a newline: {lines[-1]!r}")
    k = 0
    if lines[0].startswith("--- "):
        if len(lines) < 2 or not lines[1].startswith("+++ "):
            raise PatchError("patch line 1 is a '--- ' header not followed by a '+++ ' header")
        k = 2
    if k == len(lines):
        raise PatchError("patch has headers but no hunk")

    hunks: List[_Hunk] = []
    while k < len(lines):
        if hunks and not lines[k].startswith("@@"):
            # The previous hunk is complete, so this line is one too many for it (or stray
            # text): name that hunk, which is the one at fault.
            what = ("more lines than its header counts"
                    if lines[k][:1] in (" ", "-", "+", "\\")
                    else "expected the next '@@' hunk header after it")
            raise PatchError(f"hunk {hunks[-1].header}, patch line {k + 1}: {what}, "
                             f"found {lines[k][:-1]!r}")
        hunk, k = _parse_hunk(lines, k)
        hunks.append(hunk)
    return hunks


def _parse_hunk(lines: List[str], k: int) -> Tuple[_Hunk, int]:
    """Parse the hunk whose ``@@`` line is ``lines[k]``; return it and the next index."""
    header = lines[k][:-1]
    match = _HUNK_HEADER.fullmatch(header)
    if not match:
        raise PatchError(f"patch line {k + 1}: expected a hunk header '@@ -l,s +l,s @@', "
                         f"found {header!r}")
    old_start = _number(match.group(1), header)
    old_size = _number(match.group(2), header)
    new_size = _number(match.group(4), header)
    if old_start == 0 and old_size > 0:
        raise PatchError(f"hunk {header} removes or keeps lines starting at line 0")
    if old_size == 0 and new_size == 0:
        raise PatchError(f"hunk {header} has no lines")

    old_lines: List[str] = []
    new_lines: List[str] = []
    old_open = new_open = True  # False once a side's line had "\ No newline at end of file"
    k += 1
    while len(old_lines) < old_size or len(new_lines) < new_size:
        if k == len(lines):
            raise PatchError(f"hunk {header} ends before its lines add up to its header")
        line = lines[k]
        tag, body = line[:1], line[1:]
        old_side, new_side = tag in (" ", "-"), tag in (" ", "+")
        if not (old_side or new_side):
            raise PatchError(f"hunk {header}, patch line {k + 1}: a hunk line starts with "
                             f"' ', '-' or '+', found {line[:-1]!r}")
        if (old_side and len(old_lines) == old_size) or (new_side and len(new_lines) == new_size):
            raise PatchError(f"hunk {header}, patch line {k + 1}: more lines than its header counts")
        if (old_side and not old_open) or (new_side and not new_open):
            raise PatchError(f"hunk {header}, patch line {k + 1}: a line after "
                             f"'\\ No newline at end of file' on the same side")
        k += 1
        if k < len(lines) and lines[k].startswith("\\"):
            body = body[:-1]
            old_open = old_open and not old_side
            new_open = new_open and not new_side
            k += 1
        if old_side:
            old_lines.append(body)
        if new_side:
            new_lines.append(body)
    return _Hunk(header, old_start, old_size, old_lines, new_lines), k


def _number(digits: Optional[str], header: str) -> int:
    """Read a line number or size of a hunk header; a missing size is 1.

    ``int`` can raise the standard library's ``ValueError`` for a very long number (Python
    3.11 and later limit the digits); textkit never lets it escape (phase 3 rule "Errors"),
    so it becomes a ``PatchError``.
    """
    if digits is None:
        return 1
    try:
        return int(digits)
    except ValueError as exc:
        raise PatchError(f"hunk {header} has an unreadable number: {exc}") from None
