"""Subcommand ``python3 -m textkit render <template-file> <json-file>`` (plan task T3.4).

Renders a template file with the JSON object in another file as its context
(``textkit.template.render``) and writes the result to stdout unchanged. It follows the
phase 3 rule "The command line": both files are read as UTF-8 with ``newline=""`` (so a
``"\\r\\n"`` in the template stays ``"\\r\\n"`` in the output), the result is written with
``sys.stdout.write`` (no newline added, nothing for an empty result), and every error is
handled here and turned into an exit code:

- 0: rendered;
- 1: a ``TemplateError`` (syntax or rendering), with ``line:column: message`` on stderr;
- 2: a file that cannot be read or is not valid UTF-8, or a JSON file that is not valid JSON
  or not a JSON object, with ``python3 -m textkit render: error: <path>: <reason>`` on
  stderr. (argparse also exits 2 for a wrong argument count.)

No traceback is printed for any of them. The module registers its ``Command`` when it is
imported; ``textkit/cli/main.py`` finds and imports it (T3.1).
"""

import argparse
import json
import sys
from typing import Any

from textkit.cli.registry import PROG, Command, register
from textkit.errors import TextkitError
from textkit.template import TemplateError, render

_NAME = "render"


class _InputError(TextkitError):
    """A file of the command line that cannot be used; the message is ``<path>: <reason>``.

    A ``TextkitError`` like every exception class in ``textkit/`` (phase 3 rule "Errors",
    checked by ``tests/test_errors.py``); it never leaves this module: ``_run`` turns it into
    exit 2.
    """


def _configure(parser: argparse.ArgumentParser) -> None:
    """Add the two positional arguments: the template file and the JSON context file."""
    parser.add_argument("template", metavar="<template-file>", help="the template, UTF-8")
    parser.add_argument(
        "context", metavar="<json-file>", help="a JSON object, UTF-8: the template's context"
    )


def _read(path: str) -> str:
    """Return the text of ``path`` read as UTF-8 with no newline translation.

    Raises ``_InputError`` when the file cannot be opened or read (missing, a directory, no
    permission) or is not valid UTF-8.
    """
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except OSError as exc:
        # strerror is "No such file or directory" and the like; str(exc) would repeat the path.
        raise _InputError(f"{path}: {exc.strerror or exc}") from exc
    except UnicodeDecodeError as exc:
        raise _InputError(
            f"{path}: not valid UTF-8 (byte 0x{exc.object[exc.start]:02x} at offset {exc.start})"
        ) from exc


def _load_context(path: str) -> dict[str, Any]:
    """Return the JSON object in ``path``; ``_InputError`` if it is not one.

    ``json.loads`` raises ``ValueError`` (``JSONDecodeError``) for invalid JSON and
    ``RecursionError`` for absurdly deep nesting: both are caught here, so no
    standard-library error escapes (phase 3 rule "Errors").
    """
    text = _read(path)
    try:
        context = json.loads(text)
    except ValueError as exc:
        raise _InputError(f"{path}: not valid JSON: {exc}") from exc
    except RecursionError as exc:
        raise _InputError(f"{path}: not valid JSON: nested too deeply") from exc
    if not isinstance(context, dict):
        raise _InputError(f"{path}: not a JSON object (got a JSON {type(context).__name__})")
    return context


def _run(args: argparse.Namespace) -> int:
    """Read both files, render, write the result; return the exit code (0, 1 or 2)."""
    try:
        template = _read(args.template)
        context = _load_context(args.context)
    except _InputError as exc:
        sys.stderr.write(f"{PROG} {_NAME}: error: {exc}\n")
        return 2
    try:
        result = render(template, context)
    except TemplateError as exc:
        # str(TemplateError) is "line:column: message".
        sys.stderr.write(f"{exc}\n")
        return 1
    sys.stdout.write(result)
    return 0


COMMAND = register(
    Command(
        name=_NAME,
        summary="Render a template file with the JSON object in another file as its context.",
        configure=_configure,
        run=_run,
    )
)
