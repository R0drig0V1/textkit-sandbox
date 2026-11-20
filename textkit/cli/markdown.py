"""Tool subcommand ``python3 -m textkit markdown <file>``: a Markdown file to HTML (plan task T3.5).

Follows the phase 3 rule "The command line": the file is read as UTF-8 with ``newline=""``,
so ``to_html`` sees its ``"\\r\\n"`` and ``"\\r"`` endings as they are (it accepts all three);
the HTML is written unchanged with ``sys.stdout.write`` (nothing at all for an empty
result). Exit 0 on success; exit 2, with ``python3 -m textkit markdown: error: <path>:
<reason>`` on stderr and no traceback, when the file is missing, unreadable or not valid
UTF-8. ``to_html`` raises nothing for text, so there is no exit 1.
"""

import argparse
import sys

from textkit.cli.registry import PROG, Command, register
from textkit.markdown import to_html

NAME = "markdown"


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", help="the Markdown file to convert, read as UTF-8")


def _reason(exc: Exception) -> str:
    """A short reason for a file that cannot be read, without repeating its path."""
    if isinstance(exc, UnicodeDecodeError):
        return f"not valid UTF-8 (byte {exc.start})"
    # OSError's str() repeats the path ("[Errno 2] ...: 'x'"); strerror is the reason alone.
    return getattr(exc, "strerror", None) or str(exc)


def _run(args: argparse.Namespace) -> int:
    try:
        with open(args.file, encoding="utf-8", newline="") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"{PROG} {NAME}: error: {args.file}: {_reason(exc)}\n")
        return 2
    sys.stdout.write(to_html(text))
    return 0


COMMAND = register(
    Command(
        name=NAME,
        summary="Convert a Markdown file to HTML (textkit.markdown.to_html)",
        configure=_configure,
        run=_run,
    )
)
