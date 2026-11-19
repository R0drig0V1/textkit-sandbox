"""Command line for textkit: ``python3 -m textkit <function> <text>`` (plan task T2.6).

Prints the result of any public function that takes one text argument, and lists those
functions with ``--help``; ``--version`` prints ``textkit <version>`` from
``textkit.__version__`` (plan task T2.7). The commands are discovered at run time, never
hard-coded, so a helper added to a public module becomes a command with no change here. A
command is every public function (the definition in docs/phases/phase-1-core-helpers.md,
"Rules for every task") whose ``__module__`` is the module it is found in and that has
exactly one parameter without a default; parameters with defaults keep their default.

Output: a ``str`` result is printed as is; ``bool`` and ``int`` with ``print()``; ``dict`` and
``list`` as ``json.dumps(result, ensure_ascii=False, sort_keys=True)``. Exit status 0 on
success (``--help`` and ``--version`` included) and 2 on an unknown function, a wrong
argument count or no arguments at all, with the message (and usage) on stderr.

This module starts with ``_`` so it holds no public functions; importing it has no side
effects (``_main`` only runs under ``if __name__ == "__main__":``).
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


def _required(func: Callable[..., Any]) -> List[inspect.Parameter]:
    """Return the parameters of ``func`` that have no default and must be given a value.

    ``*args`` and ``**kwargs`` are left out: they have no default but need no value either.
    """
    return [
        p
        for p in inspect.signature(func).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]


def _commands() -> Dict[str, Callable[..., Any]]:
    """Return the command name -> function map, discovered from the public modules.

    Modules come from ``pkgutil.iter_modules(textkit.__path__)``, skipping names that start
    with ``_`` (``_tokens``, ``__main__``); functions from ``inspect.getmembers``, keeping
    only those defined in that module (so an imported helper is not a second command), whose
    name does not start with ``_`` and that have exactly one parameter without a default
    (``_required``). Sorted by name.

    Raises:
        RuntimeError: if two modules define a public function with the same name, which
            ``scripts/check.sh`` already rejects (each README row must be unique).
    """
    found: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if len(_required(func)) != 1:
                continue
            if name in found:
                raise RuntimeError(
                    f"public function {name!r} is defined in both "
                    f"{found[name].__module__} and {module.__name__}"
                )
            found[name] = func
    return dict(sorted(found.items()))


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of ``func``'s docstring, or ``""`` if it has none."""
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0] if doc else ""


def _build_parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Return the argument parser: one subcommand per entry of ``commands``.

    Kept separate from ``_main`` so that top-level options (``--version``, plan task T2.7)
    are added here, before ``add_subparsers``, without touching the dispatch.
    """
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description="Run a textkit function on one text argument and print the result.",
        epilog="Quote the text so the shell passes it as one argument.",
    )
    # argparse's version action prints to stdout and exits 0 before the required subcommand
    # is checked, so --version needs no function. The string is read from the package, never
    # repeated here, so __init__.py stays the only place the version is written.
    version = f"textkit {textkit.__version__}"
    parser.add_argument("--version", action="version", version=version)
    # On Python 3.9, required=True without dest crashes when no command is given (argparse
    # joins a None name into the error), so dest is mandatory here.
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<function>", title="functions"
    )
    for name, func in commands.items():
        doc = inspect.getdoc(func) or ""
        sub = subparsers.add_parser(
            name,
            # argparse %-formats help strings; a literal % in a docstring would crash it.
            help=_summary(func).replace("%", "%%"),
            description=doc.replace("%", "%%"),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        sub.add_argument("text", help="the text to pass to the function (quote it)")
    return parser


def _format(result: Any) -> str:
    """Return ``result`` as the CLI prints it, without the trailing newline.

    ``dict`` and ``list`` become JSON (non-ASCII kept, keys sorted); everything else,
    ``str``, ``bool`` and ``int`` included, is what ``print()`` would show.
    """
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _call(func: Callable[..., Any], text: str) -> Any:
    """Call ``func`` (a command) with ``text`` bound to its one parameter without a default."""
    (param,) = _required(func)
    if param.kind is inspect.Parameter.KEYWORD_ONLY:
        return func(**{param.name: text})
    return func(text)


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (default ``sys.argv[1:]``) and return the exit status.

    Returns 0 after printing the result, or after ``--help`` or ``--version``. Returns 2,
    with the usage and the error on stderr, for no arguments, an unknown function or a wrong
    argument count: argparse's ``SystemExit`` is caught and turned into the return value, so
    callers (and tests) get a status instead of an exception. An exception raised by the
    function itself is not caught and propagates with its traceback.
    """
    commands = _commands()
    parser = _build_parser(commands)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits with 0 (--help) or 2 (a usage error), always as an int.
        return exc.code if isinstance(exc.code, int) else 2
    print(_format(_call(commands[args.command], args.text)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
