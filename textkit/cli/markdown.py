"""The ``markdown`` tool subcommand: ``python3 -m textkit markdown <file>`` (plan task T3.5).

Reads ``<file>`` and writes ``textkit.markdown.to_html`` of it to stdout, following the
phase 3 rule "The command line":

- the file is read as UTF-8 with ``newline=""``, so ``to_html`` sees its line endings
  exactly (``"\\r\\n"`` and a lone ``"\\r"`` included) and applies its own line rule;
- the HTML is written with ``sys.stdout.write`` as it is: no newline is added, and an empty
  result writes nothing;
- exit 0 on success; exit 2, with ``python3 -m textkit markdown: error: <path>: <reason>``
  on stderr and no traceback, when the file is missing, unreadable or not valid UTF-8.
  ``to_html`` accepts every text, so there is no exit 1.

Importing the module registers the command (``textkit.cli.main._load_tools`` does it); the
module holds no public functions (``textkit.cli.__all__`` is empty).
"""

import argparse
import sys

from textkit.cli.registry import PROG, Command, register
from textkit.markdown import to_html

_NAME = "markdown"


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", help="the Markdown file to convert (read as UTF-8)")


def _error(path: str, reason: str) -> int:
    print(f"{PROG} {_NAME}: error: {path}: {reason}", file=sys.stderr)
    return 2


def _run(args: argparse.Namespace) -> int:
    """Convert ``args.file`` and write the HTML; return the exit code (0 or 2)."""
    path = args.file
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            text = handle.read()
    except UnicodeDecodeError:
        # A standard-library ValueError: it never escapes textkit (phase 3 rule "Errors").
        return _error(path, "not valid UTF-8")
    except OSError as exc:
        # Missing, a directory, no permission...: the OS reason, without the path twice.
        return _error(path, exc.strerror or type(exc).__name__)
    sys.stdout.write(to_html(text))
    return 0


_COMMAND = register(
    Command(
        name=_NAME,
        summary="Convert a Markdown file to HTML (textkit.markdown.to_html)",
        configure=_configure,
        run=_run,
    )
)
