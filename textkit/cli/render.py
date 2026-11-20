"""The ``render`` tool: ``python3 -m textkit render <template-file> <json-file>`` (plan task T3.4).

Renders the template file with ``textkit.template.render``, the context being the JSON object
in the second file, and writes the result to stdout exactly (``sys.stdout.write``: no newline
added, nothing at all for an empty result). Both files are read as UTF-8 with ``newline=""``,
so a ``"\\r\\n"`` in the template reaches the output unchanged and error columns count a
``"\\r"`` (phase 3 rule "The command line").

Exit codes: 0 rendered; 1 for a ``TemplateError`` (``TemplateSyntaxError`` included), with
``line:column: message`` on stderr; 2 for a file that is missing, unreadable or not UTF-8,
and for JSON that is invalid or not an object, with ``python3 -m textkit render: error:
<path>: <reason>`` on stderr. No traceback in any case.

Registered with ``textkit.cli.registry`` when imported (``textkit.cli.main._load_tools``);
every name here starts with ``_`` (``textkit/cli/`` has no public functions).
"""

import argparse
import json
import sys

from textkit.cli import registry
from textkit.template import TemplateError, render

_NAME = "render"


class _InputError(ValueError):
    """A file of the command could not be used; ``str()`` is ``"<path>: <reason>"``.

    Caught in ``_run`` (exit 2), never raised out of it. It subclasses ``ValueError`` only
    because the phase 3 rule "Errors" asks it of every exception class until T3.2 is merged.
    """


def _configure(parser: argparse.ArgumentParser) -> None:
    """Add the two file arguments to the ``render`` sub-parser."""
    parser.add_argument("template_file", help="the template, UTF-8 (docs/template.md)")
    parser.add_argument("json_file", help="a JSON object, UTF-8: the template's context")


def _read(path: str) -> str:
    """Return the text of ``path`` read as UTF-8 with no newline translation.

    Raises ``_InputError`` for a file that is missing, unreadable or not valid UTF-8.
    """
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except UnicodeDecodeError as exc:
        # A ValueError of the standard library: turned into this command's error (phase 3
        # rule "Errors"), never let out.
        reason = f"not valid UTF-8 ({exc.reason} at byte {exc.start})"
        raise _InputError(f"{path}: {reason}") from None
    except OSError as exc:
        raise _InputError(f"{path}: {exc.strerror or exc}") from None


def _context(path: str) -> dict:
    """Return the JSON object in ``path``; raises ``_InputError`` otherwise."""
    text = _read(path)
    try:
        value = json.loads(text)
    except ValueError as exc:  # json.JSONDecodeError
        raise _InputError(f"{path}: invalid JSON: {exc}") from None
    except RecursionError:
        raise _InputError(f"{path}: invalid JSON: nested too deeply") from None
    if not isinstance(value, dict):
        raise _InputError(f"{path}: not a JSON object (got {type(value).__name__})")
    return value


def _run(args: argparse.Namespace) -> int:
    """Render ``args.template_file`` with ``args.json_file``; return the exit code (0, 1, 2)."""
    try:
        template = _read(args.template_file)
        context = _context(args.json_file)
    except _InputError as exc:
        sys.stderr.write(f"{registry.PROG} {_NAME}: error: {exc}\n")
        return 2
    try:
        result = render(template, context)
    except TemplateError as exc:
        sys.stderr.write(f"{exc.line}:{exc.column}: {exc.message}\n")
        return 1
    sys.stdout.write(result)
    return 0


_COMMAND = registry.register(
    registry.Command(
        name=_NAME,
        summary="Render a template file with the JSON object in a second file.",
        configure=_configure,
        run=_run,
    )
)
