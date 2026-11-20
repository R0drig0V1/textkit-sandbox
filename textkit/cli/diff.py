"""The ``diff`` tool: ``python3 -m textkit diff <file-a> <file-b>`` (plan task T3.6).

Writes ``textkit.diff.unified_diff`` of the two files, as ``diff -u`` would (headers ``--- a``
and ``+++ b``). Follows the phase 3 rule "The command line": files are read as UTF-8 with
``newline=""``, so a ``"\\r\\n"`` file differs from the same text with ``"\\n"``; the result
goes to stdout unchanged through ``sys.stdout.write``; errors are handled here and turned
into the exit code. Exit codes, as ``diff``'s: 0 when the files are equal (nothing written),
1 when they differ, 2 when a file cannot be read or is not valid UTF-8.

Registered with ``textkit.cli.registry`` when imported (``textkit.cli.main._load_tools``
does it); every top-level name but ``COMMAND`` starts with ``_``, and ``textkit.cli`` has
no public functions.
"""

import argparse
import sys

from textkit.cli.registry import PROG, Command, register
from textkit.diff import unified_diff

_NAME = "diff"


def _configure(parser: argparse.ArgumentParser) -> None:
    """Add the two file arguments."""
    parser.add_argument("file_a", metavar="file-a", help="the old text (UTF-8)")
    parser.add_argument("file_b", metavar="file-b", help="the new text (UTF-8)")


def _read(path: str) -> str:
    """Return the text of ``path``, read as UTF-8 with no newline translation.

    Raises ``OSError`` for a missing or unreadable file and ``UnicodeDecodeError`` for bytes
    that are not UTF-8; ``_run`` turns both into exit 2.
    """
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _reason(exc: Exception) -> str:
    """The ``<reason>`` part of the error line for a file that could not be read."""
    if isinstance(exc, UnicodeDecodeError):
        return f"not valid UTF-8 (byte 0x{exc.object[exc.start]:02x} at offset {exc.start})"
    return getattr(exc, "strerror", None) or str(exc)


def _run(args: argparse.Namespace) -> int:
    """Diff the two files; return 0 (equal), 1 (different) or 2 (a file cannot be read).

    ``UnicodeDecodeError`` is a ``ValueError`` from the standard library: it is caught here
    so that it never escapes textkit (phase 3 rule "Errors"). This module defines no
    exception class of its own, so the T3.2 rule on their base class has nothing to check.
    """
    texts = []
    for path in (args.file_a, args.file_b):
        try:
            texts.append(_read(path))
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{PROG} {_NAME}: error: {path}: {_reason(exc)}", file=sys.stderr)
            return 2
    diff = unified_diff(texts[0], texts[1])
    if not diff:
        return 0
    sys.stdout.write(diff)
    return 1


COMMAND = register(
    Command(
        name=_NAME,
        summary="Print the unified diff (diff -u) of two UTF-8 files; exit 1 when they differ.",
        configure=_configure,
        run=_run,
    )
)
