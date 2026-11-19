"""Command line for textkit: ``python3 -m textkit <function> <text>``.

Every public function of one text argument is a command; ``python3 -m textkit --help`` lists
them with the first line of their docstring. The commands are discovered at run time, never
listed by hand, so a function added to a public module shows up here without touching this
file. A public function (the definition shared with ``scripts/check.sh`` and the plan,
docs/phases/phase-1-core-helpers.md) is a top-level ``def`` whose name does not start with
``_``, in a module of ``textkit/`` whose name does not start with ``_``; it is a command when
it has exactly one parameter without a default, a positional one. Parameters with a default
keep it (``reading_time(text, wpm=200)`` runs with ``wpm=200``).

Output: a ``str`` result is printed as is, a ``dict`` or ``list`` as
``json.dumps(result, ensure_ascii=False, sort_keys=True)``, anything else (``bool``, ``int``)
with ``print()``. Exit status: 0 on success; 2, with the message on stderr, on an unknown
function, a wrong number of arguments or no arguments at all (argparse's usage errors); 1,
with the message on stderr, if the function itself raises ``ValueError`` or ``TypeError``.
A text that starts with ``-`` goes after ``--`` (``python3 -m textkit word_count -- -x``).

This module defines no public function (its entry point is ``_main``) and importing it has
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


def _takes_one_text(func: Callable[..., Any]) -> bool:
    """Return True if ``func`` can be called with exactly one positional argument.

    That is, it has exactly one parameter without a default and that parameter can be passed
    by position. ``*args`` and ``**kwargs`` have no default but are never required, so they
    do not count; a keyword-only parameter without a default would make a one-argument call
    impossible, so it disqualifies the function. Functions whose signature cannot be read
    are not commands.
    """
    try:
        params = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):
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
    """Discover the commands: public functions of one text argument, sorted by name.

    Modules come from ``pkgutil.iter_modules(textkit.__path__)``, skipping those whose name
    starts with ``_`` (``_tokens``, this ``__main__``); functions from
    ``inspect.getmembers(module, inspect.isfunction)``, keeping only those defined in that
    module (``f.__module__``), so a helper imported from elsewhere is not listed twice.

    Raises:
        RuntimeError: if two public modules define a command with the same name, since the
            command line could not tell them apart. Fails loudly so the clash is fixed
            rather than one function silently hiding the other.
    """
    found: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if not _takes_one_text(func):
                continue
            if name in found:
                raise RuntimeError(
                    f"command {name!r} is defined in both {found[name].__module__} "
                    f"and {module.__name__}"
                )
            found[name] = func
    return dict(sorted(found.items()))


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of ``func``'s docstring, or ``""`` if it has none."""
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0].strip() if doc else ""


def _format(result: Any) -> str:
    """Render a function's result the way the command line prints it (without the newline)."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    # `str` as is; `bool`, `int` and anything else as `print()` would show it.
    return str(result)


def _parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per command, each taking one ``text``.

    The command list in ``--help`` is written into the epilog by hand, one line per command,
    instead of relying on argparse's subcommand listing, which wraps long summaries and moves
    them to the next line for long names; one line each keeps it readable and testable.
    """
    width = max((len(name) for name in commands), default=0)
    lines = [f"  {name:<{width}}  {_summary(func)}".rstrip() for name, func in commands.items()]
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run a textkit function on one text and print the result.",
        epilog="commands:\n" + "\n".join(lines),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # `dest` is mandatory with `required=True` on Python 3.9: without it, a missing command
    # crashes argparse with a TypeError instead of printing the usage and exiting 2.
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<function>", help="one of the commands below"
    )
    for name, func in commands.items():
        sub = subparsers.add_parser(
            name,
            description=inspect.getdoc(func) or None,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        sub.add_argument("text", help="the text to pass to the function (quote it)")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (``sys.argv[1:]`` when ``None``); return the exit status.

    Prints the result on stdout and returns 0. Usage errors (no arguments, an unknown
    function, a wrong number of arguments) print argparse's message on stderr and return 2;
    ``--help`` prints the help on stdout and returns 0. If the function raises ``ValueError``
    or ``TypeError``, its message goes to stderr and the status is 1.
    """
    commands = _commands()
    parser = _parser(commands)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits on --help (0) and on usage errors (2); return the status instead so
        # that `_main` can be called in-process (tests) without stopping the interpreter.
        return exc.code if isinstance(exc.code, int) else 0 if exc.code is None else 2
    func = commands[args.command]
    try:
        result = func(args.text)
    except (ValueError, TypeError) as exc:
        print(f"{parser.prog} {args.command}: error: {exc}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
