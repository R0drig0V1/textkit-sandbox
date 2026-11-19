"""The command line: ``python3 -m textkit <function> <text>`` prints ``<function>(<text>)``.

Commands are discovered at run time, never listed by hand, so a function merged later shows
up without touching this file. A command is every public function (the definition in
docs/phases/phase-1-core-helpers.md: a top-level ``def`` whose name does not start with
``_``, in a ``textkit`` module whose name does not start with ``_``) that has exactly one
parameter without a default; parameters with defaults keep them. ``truncate(text, width)``
and ``wrap(text, width)``, for example, are not commands.

Output: a ``str`` is printed as is; a ``dict`` or ``list`` as
``json.dumps(result, ensure_ascii=False, sort_keys=True)``; anything else (``bool``,
``int``) with ``print()``. Exit status: 0 on success; 2, with the message on stderr, on an
unknown function, a wrong number of arguments or no arguments at all (argparse's own
errors). Text that starts with ``-`` goes after ``--``: ``python3 -m textkit slugify -- -x``.
``python3 -m textkit --version`` prints ``textkit <textkit.__version__>`` and exits 0; it needs
no function argument.

Every name defined here starts with ``_``, so this module holds no public functions and
``scripts/check.sh`` asks for no README row. Importing it has no side effects.
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any, Callable, Dict, List, Optional

import textkit

# Parameter kinds that can never be "the" text argument (``*args``, ``**kwargs``).
_VARIADIC = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)


def _required_parameters(func: Callable[..., Any]) -> List[inspect.Parameter]:
    """Return the parameters of ``func`` that have no default and are not variadic."""
    return [
        p
        for p in inspect.signature(func).parameters.values()
        if p.default is inspect.Parameter.empty and p.kind not in _VARIADIC
    ]


def _commands() -> Dict[str, Callable[..., Any]]:
    """Map each command name to its function, discovered from the ``textkit`` modules.

    Duplicated names across modules would make a command ambiguous; the README function
    table (checked by scripts/check.sh) already forbids them, so the last module wins here.
    """
    commands: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue  # private modules (and this one) hold no public functions
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # `f.__module__` filters out functions a module merely imports.
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if len(_required_parameters(func)) == 1:
                commands[name] = func
    return commands


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of the docstring of ``func``, ready for argparse's ``help=``."""
    doc = inspect.getdoc(func) or ""
    first = doc.splitlines()[0] if doc else ""
    # argparse applies %-formatting to help strings; a literal % would crash `--help`.
    return first.replace("%", "%%")


def _call(func: Callable[..., Any], text: str) -> Any:
    """Call ``func`` with ``text`` bound to its single required parameter."""
    (param,) = _required_parameters(func)
    if param.kind is inspect.Parameter.KEYWORD_ONLY:
        return func(**{param.name: text})
    return func(text)


def _format(result: Any) -> str:
    """Render a function's result for stdout (rules in the module docstring)."""
    if isinstance(result, str):
        return result
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)  # what print() would show: bool, int and the rest


def _parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one sub-command per entry of ``commands``."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Print the result of a textkit function applied to one text argument.",
        epilog="Quote the text; text that starts with '-' goes after '--'.",
    )
    # argparse runs the "version" action while parsing and exits 0 right away, before it
    # checks the required sub-command, so `--version` works without a function argument.
    # The string comes from textkit.__version__, the only copy of the version in textkit/.
    parser.add_argument(
        "--version", action="version", version=f"textkit {textkit.__version__}"
    )
    # On Python 3.9 `required=True` needs `dest`, or the "no arguments" error itself crashes.
    sub = parser.add_subparsers(
        dest="command", required=True, metavar="function", title="functions"
    )
    for name in sorted(commands):
        func = commands[name]
        command = sub.add_parser(
            name,
            help=_summary(func),
            description=inspect.getdoc(func),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        command.add_argument("text", help="the text to pass to the function (one argument)")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (``sys.argv[1:]`` when None); return the exit status.

    Returns 0 after printing the result (or the help, or the version), and 2 after argparse has printed a
    usage error on stderr: unknown function, wrong argument count, no arguments.
    Exceptions raised by the function itself are not caught.
    """
    commands = _commands()
    try:
        args = _parser(commands).parse_args(argv)
    except SystemExit as exc:  # argparse exits on --help (0) and on usage errors (2)
        return exc.code if isinstance(exc.code, int) else 2
    print(_format(_call(commands[args.command], args.text)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
