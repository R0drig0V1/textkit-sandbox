"""Command line for textkit: ``python3 -m textkit <function> "<text>"``.

Runs one public function of one text argument and prints its result; ``--help`` lists the
functions. The commands are discovered at run time, never hard-coded, so a public function
added to any module of ``textkit/`` becomes a command with no change here.

A command is every public function (the definition in "Rules for every task" of
docs/phases/phase-1-core-helpers.md: a top-level ``def`` not starting with ``_``, in a module
of ``textkit/`` not starting with ``_``) defined in that module itself (``f.__module__``),
with exactly one parameter without a default; that parameter receives the text and every
other parameter keeps its default.

Output: a ``str`` is printed as is; a ``dict`` or ``list`` as
``json.dumps(result, ensure_ascii=False, sort_keys=True)``; anything else (``bool``, ``int``)
with ``print()``. Exit status: 0 on success; 2 on an unknown function, a wrong number of
arguments or no arguments at all, with the message (and the usage) on stderr.

This module has no public functions (its name starts with ``_``) and importing it has no
side effects: the command line only runs under ``if __name__ == "__main__":``.
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any, Callable, Dict, List, Optional

import textkit


def _takes_one_text(func: Callable[..., Any]) -> bool:
    """Return True if ``func`` has exactly one parameter without a default.

    ``*args`` and ``**kwargs`` never count (they have no default but need no argument). The
    one required parameter must also accept a positional argument, since the text is passed
    as ``func(text)``; a function whose only required parameter is keyword-only is skipped.
    """
    try:
        params = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):  # no introspectable signature: cannot be called safely
        return False
    required = [
        p
        for p in params
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    return len(required) == 1 and required[0].kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )


def _commands() -> Dict[str, Callable[..., Any]]:
    """Discover the commands: name -> function, for every public one-text-argument function.

    Modules are found with ``pkgutil.iter_modules(textkit.__path__)`` (so ``_tokens`` and
    ``__main__`` are skipped by their leading ``_``) and functions with
    ``inspect.getmembers``, keeping only those defined in the module itself so that a helper
    imported from another module is not listed twice. Function names are unique across the
    package (``scripts/check.sh`` checks the README table lists each once), so the dict loses
    nothing. Raises whatever importing a ``textkit`` module raises.
    """
    commands: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"textkit.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if _takes_one_text(func):
                commands[name] = func
    return commands


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of ``func``'s docstring, or ``""`` if it has none."""
    doc = inspect.getdoc(func)
    return doc.splitlines()[0].strip() if doc else ""


def _format(result: Any) -> str:
    """Return the text printed for ``result`` (without the final newline ``print`` adds).

    ``dict`` and ``list`` become JSON with sorted keys and non-ASCII kept as is, so the
    output is stable and machine-readable; ``str`` is unchanged; anything else, such as
    ``bool`` or ``int``, is ``str(result)``, which is what ``print()`` writes.
    """
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per command, each taking one ``text``."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run a textkit function on one text argument and print the result.",
        epilog='Quote the text: python3 -m textkit slugify "Hello, World!". '
        "Put -- before a text that starts with -.",
    )
    # dest is mandatory with required=True on Python 3.9: without it, the error message for
    # a missing command crashes argparse instead of printing the usage.
    sub = parser.add_subparsers(
        dest="command", required=True, title="commands", metavar="<function>"
    )
    for name in sorted(commands):
        # argparse expands % in help strings; a literal % in a docstring must not break it.
        summary = _summary(commands[name]).replace("%", "%%")
        command = sub.add_parser(name, help=summary, description=summary)
        command.add_argument("text", help="the text to pass to the function")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (default ``sys.argv[1:]``) and return the exit status.

    Returns 0 after printing the result (or the ``--help`` text), and 2 when argparse rejects
    the arguments (unknown function, wrong argument count, none at all), after it has
    written the usage and the message to stderr. argparse signals both by raising
    ``SystemExit``; it is caught here so that callers and tests always get an ``int``.
    An exception raised by the function itself is not caught: it is a bug, not bad input.
    """
    commands = _commands()
    try:
        args = _parser(commands).parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 2)
    print(_format(commands[args.command](args.text)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
