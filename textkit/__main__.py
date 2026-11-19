"""Command line for textkit: ``python3 -m textkit <function> "<text>"`` (plan task T2.6).

Each command is a public function of a public ``textkit`` module that takes exactly one
required argument: the text. Parameters with defaults keep their defaults. Commands are
discovered when ``_main`` runs, never listed by hand, so every new one-argument function
becomes a command with no change here. Importing this module has no side effects.

The public-function definition is the one in the "Rules for every task" section of
docs/phases/phase-1-core-helpers.md: a top-level function whose name does not start with
``_``, defined (``f.__module__``) in a module of ``textkit/`` whose name does not start with
``_``. Everything in this file is private, so ``__main__`` adds no public functions.

Output: a ``str`` result is printed as is, ``bool`` and ``int`` with ``print()``, ``dict`` and
``list`` as ``json.dumps(result, ensure_ascii=False, sort_keys=True)``. Exit codes: 0 on
success; 2 (with the usage and the message on stderr, from argparse) for an unknown function,
a wrong argument count or no arguments at all. A text that starts with ``-`` goes after
``--``: ``python3 -m textkit slugify -- "-x-"``.
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
    """Whether ``func`` has exactly one parameter without a default (the plan's rule, as is).

    Every public textkit function takes its text as its first positional parameter, so the
    command calls ``func(text)``; the other parameters keep their defaults.
    """
    params = inspect.signature(func).parameters.values()
    return sum(param.default is inspect.Parameter.empty for param in params) == 1


def _commands() -> Dict[str, Callable[..., Any]]:
    """Map each command name to its function, discovered from the ``textkit`` package now.

    Function names are unique across modules (``scripts/check.sh`` requires each public
    function to have exactly one README row), so a name never maps to two functions.
    """
    commands: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # The __module__ check drops functions a module only imports from elsewhere.
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if _takes_one_text(func):
                commands[name] = func
    return commands


def _summary(func: Callable[..., Any]) -> str:
    """The first line of ``func``'s docstring, or ``""`` when it has none."""
    doc = inspect.getdoc(func)
    return doc.splitlines()[0] if doc else ""


def _format(result: Any) -> str:
    """Render a function result for stdout by the output rules in the module docstring."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    # str is printed as is; bool, int and anything else get print()'s usual str().
    return str(result)


def _parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per command, each taking one ``text``."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run a textkit function on one text and print the result.",
        epilog='Quote the text; put it after "--" when it starts with "-".',
    )
    # dest is mandatory with required=True on Python 3.9: without it, a missing command makes
    # argparse fail with a TypeError while building the error message instead of exiting 2.
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="function", title="functions"
    )
    for name in sorted(commands):
        summary = _summary(commands[name])
        sub = subparsers.add_parser(name, help=summary, description=summary)
        sub.add_argument("text", help="the text to pass to the function")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Parse ``argv`` (``sys.argv[1:]`` when ``None``), run the command and print its result.

    Returns the exit code: 0 on success (``--help`` included), 2 when argparse rejects the
    arguments (it prints the usage and the message on stderr). An exception raised by the
    function itself is not caught.
    """
    commands = _commands()
    try:
        args = _parser(commands).parse_args(argv)
    except SystemExit as exc:
        # argparse exits for --help (0) and for usage errors (2); return the code instead so
        # that callers and tests can run _main in-process.
        return exc.code if isinstance(exc.code, int) else 2
    print(_format(commands[args.command](args.text)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
