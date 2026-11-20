"""Entry point of ``python3 -m textkit``: ``_main``, the parser and ``--version`` (T2.6, T3.1).

Two kinds of subcommand share one namespace:

- **function commands** (``textkit/cli/functions.py``): ``python3 -m textkit <function>
  <text>`` prints the result of one public function applied to one text argument;
- **tools** (``textkit/cli/registry.py``): each module ``textkit/cli/<name>.py`` registers a
  ``Command`` when imported; ``_load_tools`` imports them, ``configure`` adds their
  arguments and ``run`` returns the exit code.

``--help`` lists the function commands under ``commands:`` and, after a blank line, the tools
under ``tools:`` (no ``tools:`` block when none is registered); ``--version`` prints
``textkit <version>`` from ``textkit.__version__`` (plan task T2.7) and exits 0.

``_commands`` and ``_textkit_modules`` are imported into this module's globals and ``_main``
looks ``_textkit_modules`` up there on every call, so tests can replace it with
``mock.patch.object(textkit.cli.main, "_textkit_modules", ...)``. Importing this module has
no side effects: the tools are loaded by ``_main``, not at import time.

Every top-level name in this file starts with ``_``: the ``textkit.cli`` package has no public
functions (its ``__all__`` is empty).
"""

import argparse
import importlib
import pkgutil
import sys
from typing import Any, Callable, List, Optional

import textkit
import textkit.cli
from textkit.cli import registry
from textkit.cli.functions import (
    _call,
    _commands,
    _format,
    _summary,
    _textkit_modules,
)

_PROG = registry.PROG


def _load_tools() -> None:
    """Import every module of ``textkit/cli/`` so that each tool registers its ``Command``.

    The modules are found with ``pkgutil``, never listed by hand, so a tool is one new file.
    The package's own modules (``registry``, ``functions``, this one) are imported too: they
    register nothing, and skipping them would mean a hand-written list. Modules whose name
    starts with ``_`` are skipped. Idempotent: ``importlib`` runs a module once, and
    registering the same ``Command`` again is a no-op anyway. An import error in a tool
    propagates: a broken tool is a bug, not something to hide.
    """
    for info in pkgutil.iter_modules(textkit.cli.__path__):
        if not info.name.startswith("_"):
            importlib.import_module(f"{textkit.cli.__name__}.{info.name}")


def _check_names(
    commands: dict[str, Callable[..., Any]], tools: List[registry.Command]
) -> None:
    """Raise ``RuntimeError`` when a tool has the name of a function command.

    Both kinds share one namespace of subcommands. ``_main`` calls this after discovery and
    before parsing, so the clash fails every run (``--help`` included), not only the run that
    names the clashing subcommand.
    """
    clashes = sorted(set(commands) & {tool.name for tool in tools})
    if clashes:
        raise RuntimeError(f"tool commands named like function commands: {clashes}")


def _parser(
    commands: dict[str, Callable[..., Any]], tools: List[registry.Command]
) -> argparse.ArgumentParser:
    """Build the argument parser: one sub-command per function command and per tool.

    The lists in ``--help`` are written by hand into the description (one
    ``name  summary`` row per command under ``commands:``, then a blank line and one row per
    tool under ``tools:``) rather than left to argparse, whose layout of sub-command help
    changes between Python versions and wraps long lines; a fixed layout is also what
    ``tests/test_cli.py`` and ``tests/test_cli_registry.py`` parse. The blank line ends the
    ``commands:`` block for those parsers.
    """
    names = list(commands) + [tool.name for tool in tools]
    width = max((len(name) for name in names), default=0) + 2
    rows = "\n".join(f"  {name:<{width}}{_summary(func)}" for name, func in commands.items())
    description = (
        "Run one textkit function on one text argument and print the result, or run one "
        f"tool.\n\ncommands:\n{rows}"
    )
    if tools:
        tool_rows = "\n".join(f"  {tool.name:<{width}}{tool.summary}" for tool in tools)
        description += f"\n\ntools:\n{tool_rows}"
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=description,
        epilog=(
            "Quote the text so that the shell passes it as one argument, for example\n"
            f'  {_PROG} slugify "Hello, World!"\n'
            f'Text that starts with "-" goes after "--": {_PROG} squeeze -- "-x  y"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # The version is read from the package, never repeated here (T2.7: __init__.py is the
    # only place in textkit/ that holds the string). argparse prints it to stdout and exits
    # 0 before the required sub-command is checked, so no function argument is needed.
    parser.add_argument(
        "--version",
        action="version",
        version=f"textkit {textkit.__version__}",
        help="print the textkit version and exit",
    )
    # dest is mandatory with required=True on Python 3.9: without it, the "required"
    # error message joins a None and argparse crashes instead of printing the usage.
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="<command>",
        help="one of the commands or tools listed above",
    )
    for name, func in commands.items():
        command = sub.add_parser(name, description=_summary(func))
        command.add_argument("text", help="the text argument (quote it)")
    for tool in tools:
        tool.configure(sub.add_parser(tool.name, description=tool.summary))
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (``sys.argv[1:]`` when ``None``); return the exit code.

    Exit codes: 0 on success (and for ``--help`` and ``--version``); 2 on an unknown
    subcommand, a wrong argument count or no arguments at all, with the usage and message on
    stderr (argparse's own handling, so ``_main`` returns the code instead of raising
    ``SystemExit``); for a function command, 1 when the function raises ``ValueError`` for
    the given text, with the message on stderr; for a tool, whatever its ``run`` returns, as
    is (a tool handles its own errors: nothing it raises is caught here).

    Raises ``RuntimeError`` when two modules define the same function command, two tools
    share a name, or a tool is named like a function command (checked before parsing, so on
    every run).
    """
    _load_tools()
    commands = _commands(_textkit_modules())
    tools = registry.commands()
    _check_names(commands, tools)
    parser = _parser(commands, tools)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 after --help and 2 on a usage error; report it as a return value.
        return exc.code if isinstance(exc.code, int) else 2
    if args.command not in commands:
        tool = next(tool for tool in tools if tool.name == args.command)
        return tool.run(args)
    try:
        result = _call(commands[args.command], args.text)
    except ValueError as exc:
        print(f"{_PROG} {args.command}: error: {exc}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0
