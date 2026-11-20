"""``apply_patch`` and ``PatchError``: apply a unified diff to a text (plan task T3.6).

The patch is read in the format ``unified_diff`` writes (GNU ``diff -u``): two header lines,
then hunks. Each hunk is applied at the lines its header states, with no fuzz and no search
for a better place: a context or removed line that does not match is an error. Empty ranges
are read with GNU numbering (``l,0`` is "after line ``l``"), so a hunk from BSD ``diff``
numbered ``-1,0`` is applied after line 1. See ``docs/diff.md`` and the ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``.
"""

import re
from typing import List, NamedTuple, Optional, Tuple

from textkit.diff.lcs import split_lines
from textkit.errors import InvalidValueError

# "@@ -l[,s] +l[,s] @@", optionally followed by a space and anything (git and GNU diff -p
# write a section heading there). The numbers are ASCII digits only: \d would accept "٣".
_HUNK_HEADER = re.compile(r"@@ -([0-9]+)(?:,([0-9]+))? \+([0-9]+)(?:,([0-9]+))? @@(?: .*)?\n?")


class PatchError(InvalidValueError):
    """A patch that is not a well-formed unified diff, or that does not apply to the text.

    A subclass of ``textkit.errors.InvalidValueError`` (phase 3 rule "Errors"), so callers
    catch it with any ``TextkitError``; it is not a ``ValueError``. When a hunk is at fault,
    the message contains the hunk's ``@@`` header line.
    """


class _Hunk(NamedTuple):
    """One parsed hunk: its header line, where it starts in the old text and its lines."""

    header: str  # the "@@ ... @@" line, without its "\n", for error messages
    start: int  # index in the old text's lines of the first line the hunk covers
    old: List[str]  # context and removed lines, as they must be in the text
    new: List[str]  # context and added lines, as they replace them


def apply_patch(text: str, patch: str) -> str:
    """Return ``text`` with the unified diff ``patch`` applied to it.

    ``apply_patch(a, unified_diff(a, b)) == b`` for any two texts. ``""`` is the empty patch
    and returns ``text`` unchanged. Otherwise the patch is a ``--- `` line and a ``+++ ``
    line, each followed by anything (a file name, a timestamp, ``a/`` paths: they are
    ignored), then one or more hunks. A hunk is a header ``@@ -l,s +l,s @@`` (``,s`` left
    out when ``s`` is 1; anything after a space following the second ``@@`` is ignored)
    and exactly ``s`` old and ``s`` new lines, each starting with ``" "`` (context, in both),
    ``"-"`` (removed) or ``"+"`` (added); a ``\\`` line (``\\ No newline at end of file``)
    after a line means that line has no final ``"\\n"``. Lines of the text and of the patch
    end after each ``"\\n"``; a ``"\\r"`` is part of a line.

    Each hunk is applied at the old range its header states, with no fuzz: the old range
    starts at line ``l`` (from 1), or right after line ``l`` when it is empty (GNU numbering,
    so a BSD ``-1,0`` hunk goes after line 1). The new range's start is not used. Hunks
    must come in order and must not overlap.

    Raises:
        TypeError: if ``text`` or ``patch`` is not a ``str``.
        PatchError: (an ``InvalidValueError``) if the patch is malformed (missing or repeated
            headers, headers with no hunk, a bad hunk header, a line count that does not
            match the header, an unknown line prefix, a line with no final ``"\\n"`` in the
            patch, hunks out of order) or does not apply (a context or removed line differs
            from the text, or the range runs past its end); when a hunk is at fault, the
            message contains its ``@@`` header.
    """
    for name, value in (("text", text), ("patch", patch)):
        if not isinstance(value, str):
            raise TypeError(f"apply_patch() expects str for {name}, got {type(value).__name__}")
    if patch == "":
        return text
    lines = split_lines(text)
    out: List[str] = []
    done = 0  # lines of the old text already copied or replaced
    for hunk in _parse(patch):
        if hunk.start < done:
            raise PatchError(f"hunk out of order or overlapping the previous one: {hunk.header}")
        end = hunk.start + len(hunk.old)
        if end > len(lines):
            raise PatchError(f"hunk runs past the end of the text: {hunk.header}")
        for offset, expected in enumerate(hunk.old):
            actual = lines[hunk.start + offset]
            if actual != expected:
                raise PatchError(
                    f"line {hunk.start + offset + 1} does not match: {hunk.header}: "
                    f"expected {expected!r}, found {actual!r}"
                )
        if hunk.new and not hunk.new[-1].endswith("\n") and end < len(lines):
            # A line without "\n" can only be the last line of the result.
            raise PatchError(f"line without a newline before the end of the text: {hunk.header}")
        if out and not out[-1].endswith("\n"):
            # The previous hunk ended the text without a newline; nothing can follow it.
            raise PatchError(f"hunk after the end of the text: {hunk.header}")
        out += lines[done : hunk.start]
        out += hunk.new
        done = end
    out += lines[done:]
    return "".join(out)


def _parse(patch: str) -> List[_Hunk]:
    """Parse ``patch`` (not ``""``) into its hunks, checking that it is well formed."""
    lines = split_lines(patch)
    for number, line in enumerate(lines, 1):
        if not line.endswith("\n") and not line.startswith("\\"):
            raise PatchError(f"patch line {number} does not end in a newline: {line!r}")
    if len(lines) < 2 or not lines[0].startswith("--- ") or not lines[1].startswith("+++ "):
        raise PatchError("a patch starts with a '--- ' line and a '+++ ' line")
    if len(lines) == 2:
        raise PatchError("the patch has headers but no hunk")
    hunks: List[_Hunk] = []
    k = 2
    while k < len(lines):
        hunk, k = _parse_hunk(lines, k)
        hunks.append(hunk)
    return hunks


def _parse_hunk(lines: List[str], k: int) -> Tuple[_Hunk, int]:
    """Parse the hunk whose header is ``lines[k]``; return it and the index after it."""
    match = _HUNK_HEADER.fullmatch(lines[k])
    if not match:
        raise PatchError(f"patch line {k + 1} is not a hunk header: {lines[k]!r}")
    header = lines[k].rstrip("\n")
    old_line, old_size, _, new_size = match.groups()
    first = _number(old_line, header)
    old_count = 1 if old_size is None else _number(old_size, header)
    new_count = 1 if new_size is None else _number(new_size, header)
    if old_count == 0:
        start = first  # GNU: an empty range "l,0" is just after line l
    elif first == 0:
        raise PatchError(f"a non-empty range cannot start at line 0: {header}")
    else:
        start = first - 1
    if old_count == 0 and new_count == 0:
        raise PatchError(f"a hunk with two empty ranges changes nothing: {header}")
    old: List[str] = []
    new: List[str] = []
    last: Optional[str] = None  # the prefix of the previous body line, for a "\\" line
    body_before = ""  # that line's text
    k += 1
    while k < len(lines):
        line = lines[k]
        prefix, body = line[0], line[1:]
        if prefix == "\\":
            if last is None:
                raise PatchError(f"patch line {k + 1}: a '\\' line must follow a hunk line: {header}")
            # The line before has no final newline, on the side(s) it belongs to. An empty
            # line without a newline is no line at all, so it cannot be marked.
            if body_before == "\n":
                raise PatchError(f"patch line {k + 1}: an empty line cannot lack a newline: {header}")
            if last in " -":
                old[-1] = old[-1][:-1]
            if last in " +":
                new[-1] = new[-1][:-1]
            last = None  # a second marker in a row is an error
        elif len(old) == old_count and len(new) == new_count:
            break  # the hunk is complete; the next line starts another one
        elif prefix in " -+":
            if prefix in " -":
                old.append(body)
            if prefix in " +":
                new.append(body)
            if len(old) > old_count or len(new) > new_count:
                raise PatchError(f"the hunk has more lines than its header states: {header}")
            last, body_before = prefix, body
        elif line.startswith("@@"):
            break  # the next hunk starts before this one is complete: reported below
        else:
            raise PatchError(f"patch line {k + 1} has an unknown prefix {prefix!r}: {header}")
        k += 1
    if len(old) < old_count or len(new) < new_count:
        raise PatchError(f"the hunk has fewer lines than its header states: {header}")
    for side in (old, new):
        if any(not item.endswith("\n") for item in side[:-1]):
            raise PatchError(f"a line without a newline is not the last of its side: {header}")
    return _Hunk(header, start, old, new), k


def _number(digits: str, header: str) -> int:
    """Convert a number of a hunk header, raising ``PatchError`` when ``int`` cannot.

    The regular expression admits ASCII digits only, but Python 3.11+ (and the 3.7-3.10
    security releases since September 2022) refuse to convert more than 4300 digits with a
    plain ``ValueError``; that would escape as a standard-library error instead of the
    ``PatchError`` a malformed patch raises (phase 3 rule "Errors").
    """
    try:
        return int(digits)
    except ValueError as exc:
        raise PatchError(f"a number in the hunk header is too long: {header}") from exc
