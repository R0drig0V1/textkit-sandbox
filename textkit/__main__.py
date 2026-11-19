"""Command line for textkit: ``python3 -m textkit <function> <text>`` (plan task T2.6).

Prints the result of any public function of one text argument; ``--help`` lists them with
the first line of each docstring. The commands are discovered at run time, never hard-coded,
so a new public function becomes a command as soon as it is merged. A command is every
public function (the phase 1 definition: a top-level ``def`` whose name does not start with
``_``, in a module of ``textkit`` whose name does not start with ``_``) defined in its own
module (``f.__module__``) that has exactly one parameter without a default; parameters with
defaults keep their default.

Output: a ``str`` is printed as is, ``bool`` and ``int`` with ``print()``, ``dict`` and
``list`` as ``json.dumps(result, ensure_ascii=False, sort_keys=True)``.

``--version`` prints ``textkit <version>`` (from ``textkit.__version__``, plan task T2.7) and
exits 0; it works without a function, although a function is otherwise required.

Exit codes: 0 on success; 2 (argparse) on an unknown function, a wrong argument count or no
arguments at all, with the usage and the message on stderr; 1 when the function itself
rejects the text with ``ValueError``, with ``textkit: error: <message>`` on stderr.

This module defines no public functions (its name starts with ``_``) and importing it has no
side effects: the command line runs only under ``if __name__ == "__main__":``.
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any, Callable, Dict, List, Optional

import textkit

# Parameter kinds that take one value each; *args and **kwargs are never "without a default"
# in the sense of the plan, because a call can always leave them empty.
_SINGLE_VALUE_KINDS = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.KEYWORD_ONLY,
)


def _required_parameters(func: Callable[..., Any]) -> List[inspect.Parameter]:
    """Return the parameters of ``func`` that a call must supply (no default, not *args)."""
    return [
        p
        for p in inspect.signature(func).parameters.values()
        if p.kind in _SINGLE_VALUE_KINDS and p.default is inspect.Parameter.empty
    ]


def _commands() -> Dict[str, Callable[..., Any]]:
    """Return the command functions by name, discovered from the ``textkit`` modules.

    Imports every public module of the package (``pkgutil.iter_modules``), keeps its own
    public functions (``f.__module__ == module.__name__``, so imported helpers are not
    counted twice) and, of those, the ones with exactly one parameter without a default.
    """
    commands: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if len(_required_parameters(func)) == 1:
                commands[name] = func
    return commands


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of the docstring of ``func`` (``""`` if it has none)."""
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0] if doc else ""


def _call(func: Callable[..., Any], text: str) -> Any:
    """Call ``func`` with ``text`` as its one required parameter; the rest keep defaults."""
    (param,) = _required_parameters(func)
    if param.kind is inspect.Parameter.KEYWORD_ONLY:
        return func(**{param.name: text})
    return func(text)


def _format(result: Any) -> str:
    """Render ``result`` for stdout: JSON for ``dict`` and ``list``, ``str()`` otherwise.

    ``str()`` gives a ``str`` as is and the ``print()`` form of ``bool`` and ``int``. JSON
    keeps non-ASCII characters (``ensure_ascii=False``) and sorts keys, so the output is
    stable whatever order the function built the dict in.
    """
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _command_list(commands: Dict[str, Callable[..., Any]]) -> str:
    """Return the ``commands:`` block of ``--help``: one ``name  summary`` line per command.

    Written here rather than left to argparse because argparse wraps help text to the
    terminal width (``COLUMNS``) and moves long command names onto a line of their own, so
    its list would change with the terminal; this one is the same everywhere.
    """
    width = max((len(name) for name in commands), default=0)
    lines = [f"  {name.ljust(width)}  {_summary(commands[name])}".rstrip()
             for name in sorted(commands)]
    return "\n".join(["commands:", *lines])


def _parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per command, each taking one ``text``."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Print the result of a textkit function applied to one text argument.",
        epilog="\n\n".join([
            _command_list(commands),
            "Quote the text so that the shell passes it as one argument.\n"
            "Put -- before a text that starts with -: python3 -m textkit slugify -- -x",
        ]),
        # Keep the epilog's line breaks (the command list is pre-formatted).
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # The version action prints and exits as soon as it is parsed, before argparse checks
    # for the required subcommand, so "--version" alone is enough. The string is read from
    # textkit.__version__, the only place it is written.
    parser.add_argument(
        "--version", action="version", version=f"textkit {textkit.__version__}",
    )
    # On Python 3.9, required subparsers need a dest: without it a missing command raises
    # TypeError inside argparse instead of printing the usage.
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<function>",
        help="the function to run (see the commands below)",
    )
    for name in sorted(commands):
        # No help= here: argparse would list the command a second time, wrapped.
        summary = _summary(commands[name])
        sub = subparsers.add_parser(name, description=summary)
        sub.add_argument("text", help="the text to pass to the function")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (``sys.argv[1:]`` when ``None``); return the exit code.

    Returns 0 after printing the result, 2 when argparse rejects the arguments (unknown
    function, wrong argument count, none at all; argparse prints the usage and the message
    on stderr) and 1 when the function raises ``ValueError``. ``--help`` and ``--version``
    print the help or the version and return 0. Other exceptions propagate: they are bugs, and the traceback is the report.
    """
    commands = _commands()
    try:
        args = _parser(commands).parse_args(argv)
    except SystemExit as exit_:
        # argparse exits on --help and --version (0) and on errors (2); return the code instead so that
        # _main can be called in-process.
        return exit_.code if isinstance(exit_.code, int) else 2
    try:
        result = _call(commands[args.command], args.text)
    except ValueError as error:
        print(f"textkit: error: {error}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
