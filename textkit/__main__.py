"""Command line for textkit: ``python3 -m textkit <function> <text>`` (plan task T2.6).

Prints the result of any public function of one text argument, and lists them with
``--help``. Commands are discovered at run time, never hard-coded, so a function added to a
public module becomes a command with no change here. A command is every *public function*
(phase 1 definition: a top-level ``def`` whose name does not start with ``_``, in a module of
``textkit/`` whose name does not start with ``_``) that has exactly one parameter without a
default; parameters with a default keep it (``reading_time(text, wpm=200)`` runs with 200).

Output: a ``str`` is printed as is; ``bool`` and ``int`` with ``print()``; ``dict`` and
``list`` as ``json.dumps(result, ensure_ascii=False, sort_keys=True)``. Exit status: 0 on
success; 2 on an unknown function, a wrong argument count or no arguments at all (argparse
prints the usage and the message on stderr); 1 when the function itself rejects the text
with ``ValueError`` (the message goes to stderr). The plan fixes 0 and 2; 1 keeps a rejected
input apart from a usage error. Any other exception is a bug and propagates as a traceback.

This module defines no public function (its name starts with ``_``), and importing it has
no side effects: the command line only runs under ``if __name__ == "__main__":``.
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any, Callable, Dict, List, Optional

import textkit

_PROG = "python3 -m textkit"


def _required_params(func: Callable[..., Any]) -> List[inspect.Parameter]:
    """Return the parameters of ``func`` that have no default.

    ``*args`` and ``**kwargs`` are left out: they have no default but never need a value.
    """
    variadic = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    return [
        p
        for p in inspect.signature(func).parameters.values()
        if p.kind not in variadic and p.default is inspect.Parameter.empty
    ]


def _commands() -> Dict[str, Callable[..., Any]]:
    """Discover the commands: public functions with exactly one parameter without a default.

    Modules are found with ``pkgutil.iter_modules(textkit.__path__)`` and functions with
    ``inspect.getmembers``; a function counts only in the module that defines it
    (``f.__module__``), so a name imported from another module is not listed twice.
    Function names are unique across modules (``scripts/check.sh`` enforces one README row
    per name); modules are visited in sorted order so the result is deterministic anyway.
    Returns the commands keyed by function name, sorted by name.
    """
    found: Dict[str, Callable[..., Any]] = {}
    for info in sorted(pkgutil.iter_modules(textkit.__path__), key=lambda i: i.name):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if len(_required_params(func)) == 1:
                found[name] = func
    return dict(sorted(found.items()))


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of the docstring of ``func``, or ``""`` if it has none."""
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0] if doc else ""


def _call(func: Callable[..., Any], text: str) -> Any:
    """Call ``func`` with ``text`` as its one parameter without a default.

    A keyword-only parameter is passed by name; any other kind by position (a
    positional-only one would reject a keyword).
    """
    (param,) = _required_params(func)
    if param.kind is inspect.Parameter.KEYWORD_ONLY:
        return func(**{param.name: text})
    return func(text)


def _format(result: Any) -> str:
    """Render a command's result as the line printed on stdout (without the newline).

    ``dict`` and ``list`` become JSON with sorted keys and non-ASCII kept as is; everything
    else (``str``, ``bool``, ``int``) is what ``print()`` would show.
    """
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one sub-command per command, each taking one ``text``."""
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description="Run a textkit function on one text argument and print the result.",
        epilog="Quote the text so the shell passes it as one argument.",
        # Raw text keeps each command's summary on one line, so the list in --help reads as
        # one "name  summary" row per command (long names still put the summary below).
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # dest is mandatory with required=True on Python 3.9: without it, running with no
    # arguments crashes inside argparse instead of printing the usage and exiting 2.
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<function>", title="functions"
    )
    for name, func in commands.items():
        sub = subparsers.add_parser(
            name,
            help=_summary(func),
            description=inspect.getdoc(func),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        sub.add_argument("text", help="the input text (quote it)")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (default ``sys.argv[1:]``) and return the exit status.

    Returns 0 on success (``--help`` included), 2 on a usage error and 1 when the function
    raises ``ValueError``; see the module docstring. argparse reports usage errors by raising
    ``SystemExit``; it is caught here so that callers (and tests) always get an ``int``.
    """
    commands = _commands()
    try:
        args = _parser(commands).parse_args(argv)
    except SystemExit as exc:
        # argparse exits with an int status (0 for --help, 2 for errors).
        return exc.code if isinstance(exc.code, int) else 2
    try:
        result = _call(commands[args.command], args.text)
    except ValueError as exc:
        print(f"{_PROG} {args.command}: error: {exc}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
