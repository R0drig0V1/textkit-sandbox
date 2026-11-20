"""``_main``: parser and dispatch of ``python3 -m textkit`` (plan tasks T2.6, T2.7, T3.1, T3.2).

Two kinds of subcommand share one namespace of names:

- function commands, ``python3 -m textkit <function> <text>``: one per public function of
  textkit that takes one text argument (``textkit/cli/functions.py``, T2.6). The result is
  printed; a ``TextkitError`` from the function (``textkit/errors.py``, T3.2) exits 1 with
  its message. Any other exception, a plain ``ValueError`` included, is a bug in textkit and
  propagates with its traceback (ADR 0006).
- tools, ``python3 -m textkit <name> ...``: one per ``Command`` registered by a module
  ``textkit/cli/<name>.py`` (``textkit/cli/registry.py``). ``_main`` lets the tool add its
  arguments, then returns the exit code of ``Command.run`` as is.

``--help`` lists the function commands under ``commands:`` and, after a blank line, the tools
under ``tools:`` (no ``tools:`` block when none is registered); ``--version`` prints
``textkit <version>`` from ``textkit.__version__`` (T2.7) and exits 0.

Tool modules are imported by ``_load_tools``, which ``_main`` calls, never when this module is
imported: importing it has no side effects. ``_main`` looks ``_textkit_modules`` up in this
module's globals on every call, so tests can replace it with ``mock.patch.object``.
"""

import argparse
import importlib
import pkgutil
import sys
from typing import Any, Callable, Dict, List, Optional

import textkit
import textkit.cli
from textkit.cli import registry
from textkit.cli.functions import _call, _commands, _format, _summary, _textkit_modules
from textkit.cli.registry import PROG, Command
from textkit.errors import TextkitError

# The modules of textkit/cli/ that are the command line itself, not tools.
_MACHINERY = frozenset({"functions", "main", "registry"})


def _tool_module_names() -> List[str]:
    """Return the full names of the tool modules of ``textkit/cli/``, sorted.

    A tool module is any module of the package (found with ``pkgutil``, never listed by hand)
    whose name does not start with ``_`` and that is not part of the machinery
    (``functions``, ``main``, ``registry``). ``textkit.cli.__path__`` is read on every call.
    """
    return sorted(
        f"{textkit.cli.__name__}.{info.name}"
        for info in pkgutil.iter_modules(textkit.cli.__path__)
        if not info.name.startswith("_") and info.name not in _MACHINERY
    )


def _load_tools() -> None:
    """Import every tool module, so that each registers its ``Command``.

    Idempotent: a module already imported is not executed again (``importlib`` returns it
    from ``sys.modules``), so calling it twice registers nothing twice. An import error
    propagates: a broken tool is a bug, not something to hide.
    """
    for name in _tool_module_names():
        importlib.import_module(name)


def _rows(entries: Dict[str, str]) -> str:
    """Format ``name -> summary`` as aligned ``  name  summary`` lines, one per entry."""
    width = max((len(name) for name in entries), default=0) + 2
    return "\n".join(f"  {name:<{width}}{summary}" for name, summary in entries.items())


def _parser(
    commands: Dict[str, Callable[..., Any]], tools: List[Command]
) -> argparse.ArgumentParser:
    """Build the argument parser: one sub-command per function command and per tool.

    A function command takes one ``text``; a tool's parser gets its arguments from
    ``Command.configure``. The lists in ``--help`` are written by hand into the description
    (``name  first docstring line`` rows under ``commands:``, then ``name  summary`` rows
    under ``tools:``) rather than left to argparse, whose layout of sub-command help changes
    between Python versions and wraps long lines; a fixed layout is also what
    ``tests/test_cli.py`` and ``tests/test_cli_registry.py`` parse. With no tool registered,
    the help is exactly what it was before tools existed (T3.1: behaviour does not change).
    """
    description = (
        "Run one textkit function on one text argument and print the result.\n\n"
        f"commands:\n{_rows({name: _summary(func) for name, func in commands.items()})}"
    )
    if tools:
        description += f"\n\ntools:\n{_rows({tool.name: tool.summary for tool in tools})}"
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=description,
        epilog=(
            "Quote the text so that the shell passes it as one argument, for example\n"
            f'  {PROG} slugify "Hello, World!"\n'
            f'Text that starts with "-" goes after "--": {PROG} squeeze -- "-x  y"'
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
        # "<function>" and its help are those of T2.6; with tools, the word covers both kinds.
        metavar="<command>" if tools else "<function>",
        help=f"one of the {'commands or tools' if tools else 'commands'} listed above",
    )
    for name, func in commands.items():
        command = sub.add_parser(name, description=_summary(func))
        command.add_argument("text", help="the text argument (quote it)")
    for tool in tools:
        tool.configure(sub.add_parser(tool.name, description=tool.summary))
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (``sys.argv[1:]`` when ``None``); return the exit code.

    Exit codes: 0 on success (and for ``--help`` and ``--version``); 2 on an unknown command,
    a wrong argument count or no arguments at all, with the usage and message on stderr
    (argparse's own handling, so ``_main`` returns the code instead of raising
    ``SystemExit``); for a function command, 1 when the function raises ``TextkitError`` for
    the given text, with the message on stderr and no traceback; for a tool, whatever
    ``Command.run`` returns. Only function commands are wrapped in ``except TextkitError``: a
    tool handles its own errors. A plain ``ValueError`` is not caught: textkit never raises
    one on purpose, so one that escapes is a bug and keeps its traceback (ADR 0006).

    Raises ``RuntimeError`` when a tool has the name of a function command. It is checked
    after discovery and before parsing, so the clash fails every run (``--help`` included),
    not just the runs of that name.
    """
    _load_tools()
    commands = _commands(_textkit_modules())
    tools = registry.commands()
    clashes = sorted(tool.name for tool in tools if tool.name in commands)
    if clashes:
        raise RuntimeError(f"tool commands named like function commands: {clashes}")
    parser = _parser(commands, tools)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 after --help and 2 on a usage error; report it as a return value.
        return exc.code if isinstance(exc.code, int) else 2
    for tool in tools:
        if tool.name == args.command:
            return tool.run(args)
    try:
        result = _call(commands[args.command], args.text)
    except TextkitError as exc:
        print(f"{PROG} {args.command}: error: {exc}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0
