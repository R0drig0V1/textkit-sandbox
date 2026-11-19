"""Command line for textkit: ``python3 -m textkit <function> <text>``.

Prints the result of a textkit public function called on one text argument, and lists the
available functions with ``--help``.

Commands are discovered at run time, never hard-coded, so a function added to any public
module becomes a command with no edit here. A command is every public function (a top-level
``def`` not starting with ``_``, in a ``textkit`` module not starting with ``_``; phase 1
"Rules for every task") that is defined in that module (``f.__module__``) and has exactly
one parameter without a default. Parameters with a default keep it; a function with two
required parameters (``wrap``, ``truncate``) is not a command.

Argument: exactly one, quoted when it has spaces. An argument that starts with ``-`` and is
not an integer reads as an option, so put ``--`` before it (``python3 -m textkit slugify --
-x``). When the required parameter is annotated ``int``, the argument must satisfy
``re.fullmatch(r"-?[0-9]+", arg)`` (ASCII digits only) and is converted with ``int(arg)``.

Output: a ``str`` is printed as is; a ``dict`` or ``list`` as
``json.dumps(result, ensure_ascii=False, sort_keys=True)``; anything else (``bool``,
``int``) with ``print()``.

Exit codes: 0 on success; 1 when the function, or printing its result, raises
``ValueError``, ``KeyError`` or ``TypeError`` (``error: <message>`` on stderr, no traceback;
a ``UnicodeEncodeError`` from a terminal that cannot show the result is a ``ValueError``);
2 on an unknown function, a wrong argument count, no arguments, or an ``int`` argument that
is not an integer or that ``int()`` rejects (argparse's usage and message on stderr).
Importing this module has no side effects.
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

# ASCII digits only: int() alone would accept "٣", " 5", "+5" and "1_000".
_INT_ARGUMENT = re.compile(r"-?[0-9]+")


def _required_parameter(function: Callable[..., object]) -> Optional[inspect.Parameter]:
    """Return the only parameter of ``function`` without a default, or None.

    ``*args`` and ``**kwargs`` never count: they cannot receive the one text argument as a
    required value. None means the function is not a command (zero or several required
    parameters).
    """
    required = [
        p
        for p in inspect.signature(function).parameters.values()
        if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
    ]
    return required[0] if len(required) == 1 else None


def _wants_int(function: Callable[..., object], parameter: inspect.Parameter) -> bool:
    """Tell whether ``parameter`` of ``function`` is annotated ``int``.

    Annotations are resolved with ``typing.get_type_hints`` (string annotations included);
    if they do not evaluate, the raw annotation is used instead, so a broken hint elsewhere
    in the signature does not make the command unusable.
    """
    try:
        annotation = typing.get_type_hints(function).get(parameter.name)
    except Exception:  # an unevaluable hint is that function's bug, not the CLI's
        annotation = parameter.annotation
    return annotation is int


def _commands() -> Dict[str, Callable[..., object]]:
    """Discover the commands: name -> function, modules in ``pkgutil`` order.

    If two modules define the same name, the first one found wins (argparse on newer
    Pythons rejects a duplicate sub-command, which would break every invocation).
    """
    commands: Dict[str, Callable[..., object]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or function.__module__ != module.__name__:
                continue
            if name not in commands and _required_parameter(function) is not None:
                commands[name] = function
    return commands


def _int_argument(text: str) -> int:
    """Convert a command-line argument to ``int``; argparse turns the error into exit 2."""
    if not _INT_ARGUMENT.fullmatch(text):
        raise argparse.ArgumentTypeError(f"expected an integer (-?[0-9]+), got {text!r}")
    try:
        return int(text)
    except ValueError as error:  # e.g. more digits than sys.get_int_max_str_digits() allows
        raise argparse.ArgumentTypeError(str(error)) from error


def _first_line(function: Callable[..., object]) -> str:
    """The first line of the docstring, escaped for argparse (which %-formats help)."""
    doc = inspect.getdoc(function) or ""
    return doc.splitlines()[0].replace("%", "%%") if doc else ""


def _build_parser(commands: Dict[str, Callable[..., object]]) -> argparse.ArgumentParser:
    """One sub-command per function, each with its required parameter as the positional."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run a textkit function on one text argument and print the result.",
    )
    # dest is mandatory with required=True on Python 3.9, or no arguments crashes.
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<function>")
    for name, function in sorted(commands.items()):
        parameter = _required_parameter(function)
        assert parameter is not None  # _commands keeps only functions that have one
        sub = subparsers.add_parser(name, help=_first_line(function), description=_first_line(function))
        # dest is fixed so a parameter named "command" cannot clash with the sub-command.
        if _wants_int(function, parameter):
            sub.add_argument("value", metavar=parameter.name, type=_int_argument, help="an integer")
        else:
            sub.add_argument("value", metavar=parameter.name, help="the text (quote it)")
    return parser


def _format(result: object) -> str:
    """Render a result as described in the module docstring."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (default ``sys.argv[1:]``) and return the exit code.

    argparse's own exits (``--help``, usage errors) are caught and returned as codes, so the
    function can be called in-process; see the module docstring for the codes.
    """
    commands = _commands()
    parser = _build_parser(commands)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return exit_.code if isinstance(exit_.code, int) else 2
    function = commands[args.command]
    parameter = _required_parameter(function)
    assert parameter is not None
    value = args.value
    try:
        if parameter.kind is parameter.KEYWORD_ONLY:
            result = function(**{parameter.name: value})
        else:
            result = function(value)
        # Printing is inside the handler: a UnicodeEncodeError (a ValueError) on a terminal
        # that cannot encode the result is a user-facing error, not a traceback.
        print(_format(result))
    except (ValueError, KeyError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main())
