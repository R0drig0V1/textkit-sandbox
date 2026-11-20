"""Tool subcommand ``python3 -m textkit diff <file-a> <file-b>`` (plan task T3.6).

Prints ``textkit.diff.unified_diff`` of the two files, its headers ``--- a`` and ``+++ b`` as
the function gives them. Exit codes follow ``diff``: 0 when the files are equal (nothing is
written), 1 when they differ, 2 when a file cannot be read. The files are read as UTF-8 with
``newline=""``, so the function sees them exactly: a file with ``"\\r\\n"`` endings differs
from the same text with ``"\\n"`` endings (phase 3 rule "The command line").

Every top-level name here starts with ``_``: the module holds no public functions. It
registers its ``Command`` when ``textkit/cli/main.py`` imports it.
"""

import argparse
import sys

from textkit.cli.registry import PROG, Command, register
from textkit.diff import unified_diff


def _configure(parser: argparse.ArgumentParser) -> None:
    """Add the two file arguments."""
    parser.add_argument("file_a", metavar="file-a", help="the old text (the - lines)")
    parser.add_argument("file_b", metavar="file-b", help="the new text (the + lines)")


def _read(path: str) -> str:
    """Return the text of ``path``, UTF-8, with no newline translation.

    Raises ``OSError`` or ``UnicodeDecodeError``, which ``_run`` reports.
    """
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _reason(exc: Exception) -> str:
    """A short reason for a file that cannot be read, without repeating its path."""
    if isinstance(exc, UnicodeDecodeError):
        return f"not valid UTF-8 ({exc.reason} at byte {exc.start})"
    if isinstance(exc, OSError) and exc.strerror:
        return exc.strerror
    return str(exc)


def _run(args: argparse.Namespace) -> int:
    """Write the unified diff of the two files; return 0 (equal), 1 (different) or 2 (error)."""
    texts = []
    for path in (args.file_a, args.file_b):
        try:
            texts.append(_read(path))
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{PROG} diff: error: {path}: {_reason(exc)}", file=sys.stderr)
            return 2
    diff = unified_diff(texts[0], texts[1])
    if not diff:
        return 0
    sys.stdout.write(diff)
    return 1


register(
    Command(
        "diff",
        "Print the unified diff of two files (exit 0 equal, 1 different, 2 error)",
        configure=_configure,
        run=_run,
    )
)
