"""Command line for textkit: ``python3 -m textkit <function> <text>`` (plan tasks T2.6, T2.7).

Every public function (phase 1 definition: a top-level ``def`` whose name does not start
with ``_``, in a module of ``textkit/`` whose name does not start with ``_``) that has
exactly one parameter without a default becomes a command of the same name. Commands are
discovered at run time by ``_commands()``, so a new function needs no change here.

Usage::

    python3 -m textkit slugify "Hello, World!"     # hello-world
    python3 -m textkit to_roman 1994               # MCMXCIV
    python3 -m textkit slugify -- -x               # x  (`--` before a text starting with -)
    python3 -m textkit --help                      # every command and its summary
    python3 -m textkit --version                   # textkit <textkit.__version__>

Behaviour:

- The argument of a parameter annotated ``int`` must match ``-?[0-9]+`` (ASCII digits only)
  and is converted with ``int()``; anything else is passed as the ``str`` typed.
- Output: a ``str`` is printed as is; ``dict`` and ``list`` as sorted, non-ASCII-escaped
  JSON; anything else (``bool``, ``int``) with ``print()``.
- Exit codes: 0 on success; 1 when the function, or printing its result, raises
  ``ValueError``, ``KeyError`` or ``TypeError`` (``error: <message>`` on stderr, no
  traceback); 2 for an unknown function, a wrong argument count, an argument that is not an
  integer where one is needed, or no arguments at all (argparse prints the usage on stderr).
- ``--version`` prints ``textkit <textkit.__version__>`` on stdout and exits 0, before any
  command is required.

The module has no public functions (its name starts with ``_``), and importing it has no
side effects: the command line only runs under ``if __name__ == "__main__":``.
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import re
import sys
import typing
from typing import Callable, Dict, List, Optional

import textkit

# ASCII digits only: `\d` and `int()` also accept other scripts' digits ("٣"), which the
# plan rules out so that the accepted syntax is the same on every platform and locale.
_INT_RE = re.compile(r"-?[0-9]+")

# The exceptions a textkit function may raise on bad input (phase-3 rule). Anything else is
# a bug and keeps its traceback.
_FUNCTION_ERRORS = (ValueError, KeyError, TypeError)


def _required_parameter(func: Callable[..., object]) -> Optional[inspect.Parameter]:
    """Return the only parameter of ``func`` without a default, or ``None``.

    ``*args`` and ``**kwargs`` never count as required (they have no default but need no
    value). ``None`` is returned when there are zero or several required parameters, or when
    ``func`` has no inspectable signature (some builtins).
    """
    try:
        params = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):
        return None
    required = [
        p
        for p in params
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    return required[0] if len(required) == 1 else None


def _commands() -> Dict[str, Callable[..., object]]:
    """Discover the commands: name -> function, for every eligible public function.

    Walks the modules of the ``textkit`` package (skipping names that start with ``_``,
    this one included), keeps the functions defined in that module (``f.__module__`` equal to
    the module's name, so imported helpers are not listed twice) whose name does not start
    with ``_``, and of those the ones with exactly one parameter without a default. An import
    error in a module propagates: it is a bug in that module, not bad input.

    Function names are unique across the package (``scripts/check.sh`` enforces one README
    row per name), so the flat namespace has no collisions.
    """
    commands: Dict[str, Callable[..., object]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if _required_parameter(func) is not None:
                commands[name] = func
    return dict(sorted(commands.items()))


def _parameter_of(name: str, func: Callable[..., object]) -> inspect.Parameter:
    """Return the required parameter of command ``name``.

    Raises ``TypeError`` when ``func`` does not have exactly one parameter without a
    default: ``_commands()`` never returns such a function, so this is a programming error
    (for example a test stub that breaks the rule) and keeps its traceback.
    """
    param = _required_parameter(func)
    if param is None:
        raise TypeError(f"command {name!r} does not take exactly one required argument")
    return param


def _summary(func: Callable[..., object]) -> str:
    """First line of the docstring of ``func``, or ``""`` when it has none."""
    doc = inspect.getdoc(func)
    return doc.splitlines()[0].strip() if doc else ""


def _is_int_parameter(func: Callable[..., object], param: inspect.Parameter) -> bool:
    """Tell whether ``param`` of ``func`` is annotated ``int``.

    Uses ``typing.get_type_hints`` so that string annotations are resolved too; if they do
    not evaluate (T2.5 makes that a test failure), falls back to the raw annotation.
    """
    try:
        hint = typing.get_type_hints(func).get(param.name, param.annotation)
    except Exception:  # noqa: BLE001 - any evaluation error means "use the raw annotation"
        hint = param.annotation
    return hint is int


def _to_int(arg: str) -> int:
    """Convert a command-line argument to ``int`` for a parameter annotated ``int``.

    Raises ``argparse.ArgumentTypeError`` (argparse turns it into exit 2 with the message on
    stderr) unless ``arg`` is an optional ``-`` followed by ASCII digits, or when ``int()``
    itself refuses it (Python 3.11+ limits integer strings to 4300 digits by default).
    """
    if not _INT_RE.fullmatch(arg):
        raise argparse.ArgumentTypeError(f"not an integer: {arg!r}")
    try:
        return int(arg)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a usable integer: {exc}") from None


def _build_parser(commands: Dict[str, Callable[..., object]]) -> argparse.ArgumentParser:
    """Build the parser: one sub-command per entry of ``commands``, one positional each.

    The command list of ``--help`` is written into the epilog by hand (one
    ``  <name>  <summary>`` line per command) instead of argparse's per-choice help, because
    argparse %-formats choice help strings (a docstring with ``%`` would crash it) and wraps
    long names unpredictably; the hand-written block is stable enough for the tests to parse.
    """
    width = max((len(name) for name in commands), default=0)
    lines = [f"  {name.ljust(width)}  {_summary(func)}".rstrip() for name, func in commands.items()]
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run one textkit function on one argument and print the result.",
        epilog="commands:\n" + "\n".join(lines) + "\n\n"
        "Quote the argument; put `--` before it when it starts with `-` and is not an integer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # argparse's "version" action prints and exits 0 while parsing, so the required
    # sub-command is never asked for. The string comes from textkit.__version__ (T2.7: the
    # version appears nowhere else in textkit/).
    parser.add_argument("--version", action="version", version=f"textkit {textkit.__version__}")
    # `dest` is mandatory with required=True on Python 3.9: without it, the error message
    # for a missing command crashes argparse with a TypeError.
    sub = parser.add_subparsers(
        dest="command", required=True, metavar="<function>", help="one of the commands below"
    )
    for name, func in commands.items():
        param = _parameter_of(name, func)
        command = sub.add_parser(name, description=_summary(func) or None)
        command.add_argument(
            "argument", metavar=param.name, type=_to_int if _is_int_parameter(func, param) else str
        )
    return parser


def _format(result: object) -> str:
    """Render a function's result as the line(s) to print (without the final newline)."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (default ``sys.argv[1:]``) and return the exit code.

    Returns 0 on success and 1 when the function or printing its result raises
    ``ValueError``, ``KeyError`` or ``TypeError`` (``error: <message>`` on stderr; a
    ``UnicodeEncodeError`` from a stdout that cannot encode the result is a ``ValueError``).
    Usage errors (unknown function, wrong argument count, a non-integer for an ``int``
    parameter, no arguments) raise ``SystemExit(2)`` from argparse, after it prints the
    usage and the message on stderr; ``--help`` and ``--version`` raise ``SystemExit(0)``.
    """
    commands = _commands()
    args = _build_parser(commands).parse_args(argv)
    func = commands[args.command]
    param = _parameter_of(args.command, func)
    # A keyword-only required parameter cannot be passed positionally; the others can, and
    # parameters with defaults keep their default either way.
    if param.kind is inspect.Parameter.KEYWORD_ONLY:
        positional, keywords = (), {param.name: args.argument}
    else:
        positional, keywords = (args.argument,), {}
    try:
        # Printing is inside the handler: an unencodable result must exit 1, not crash.
        print(_format(func(*positional, **keywords)))
    except _FUNCTION_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main())
