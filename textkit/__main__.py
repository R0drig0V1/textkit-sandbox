"""Command line for textkit: ``python3 -m textkit <function> "<text>"``.

Prints the result of any public function of one text argument and lists them with
``--help``; ``--version`` prints ``textkit <textkit.__version__>``. The commands are
discovered at run time, never hard-coded: every public function (the phase 1 definition:
a top-level function whose name does not start with ``_``, in a ``textkit`` module whose
name does not start with ``_``) defined in its own module and with exactly one parameter
without a default. Parameters with defaults keep their default. A new function that
fits becomes a command with no change here.

Importing this module has no side effects; ``_main`` only runs under
``if __name__ == "__main__":``. Usage and output rules are in docs/cli.md.
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any, Callable, Dict, List, Optional

import textkit

# Parameter kinds that can receive the text argument; *args and **kwargs never count as the
# one required parameter and never make a function a non-command.
_NAMED_KINDS = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.KEYWORD_ONLY,
)


def _required_parameter(func: Callable[..., Any]) -> Optional[inspect.Parameter]:
    """Return the only parameter of ``func`` without a default, or None if it has 0 or 2+."""
    try:
        params = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):  # no introspectable signature: not a command
        return None
    required = [p for p in params if p.kind in _NAMED_KINDS and p.default is p.empty]
    return required[0] if len(required) == 1 else None


def _commands() -> Dict[str, Callable[..., Any]]:
    """Discover the commands: public one-text-argument functions of the public modules.

    Modules come from ``pkgutil.iter_modules(textkit.__path__)`` and functions from
    ``inspect.getmembers(module, inspect.isfunction)``, keeping only those whose
    ``__module__`` is that module (so a helper imported from another module is not listed
    twice). Sorted by name so ``--help`` is stable.

    Raises:
        RuntimeError: if two modules define a command with the same name, since one
            would silently hide the other (the README table already requires unique names).
    """
    found: Dict[str, Callable[..., Any]] = {}
    for info in pkgutil.iter_modules(textkit.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{textkit.__name__}.{info.name}")
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if _required_parameter(func) is None:
                continue
            if name in found:
                raise RuntimeError(f"command {name!r} is defined in two modules")
            found[name] = func
    return dict(sorted(found.items()))


def _first_doc_line(func: Callable[..., Any]) -> str:
    """Return the first line of ``func``'s docstring, or "" when it has none."""
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0].strip() if doc else ""


def _build_parser(commands: Dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per command, each taking one ``text``."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run a textkit function on one text argument and print the result.",
        epilog='Quote the text: python3 -m textkit slugify "Hello, World!". '
        "Use -- before a text that starts with -.",
    )
    # The version is read from textkit.__version__, its only definition, never repeated here.
    # action="version" prints to stdout and exits 0 before the required subcommand is checked.
    parser.add_argument(
        "--version", action="version", version=f"textkit {textkit.__version__}"
    )
    # dest is mandatory with required=True on Python 3.9: without it, argparse crashes
    # with a TypeError while building the "required" error message.
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<function>", title="functions"
    )
    for name, func in commands.items():
        # argparse %-formats help and description strings, so a literal % must be doubled.
        line = _first_doc_line(func).replace("%", "%%")
        sub = subparsers.add_parser(name, help=line, description=line)
        sub.add_argument("text", help="the text to pass to the function (quote it)")
    return parser


def _format(result: Any) -> str:
    """Render a result for stdout: dict and list as sorted JSON, everything else as print()."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    # str is printed as is; bool and int (and anything else) as print() would show them.
    return str(result)


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line and return the exit status.

    ``argv`` defaults to ``sys.argv[1:]``. Prints the result of the chosen function to
    stdout and returns 0. An unknown function, a wrong argument count or no arguments at
    all print the usage and an error to stderr and return 2; ``--help`` prints the list of
    functions to stdout and returns 0, and so does ``--version`` with ``textkit <version>``.
    A ``ValueError`` raised by the function itself is reported on stderr as
    ``textkit: error: <message>`` and returns 1 (no traceback).
    """
    commands = _commands()
    parser = _build_parser(commands)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 2 on usage errors and 0 after --help; return the code instead so
        # that _main can be called in-process (tests) without stopping the interpreter.
        return exc.code if isinstance(exc.code, int) else 2
    func = commands[args.command]
    param = _required_parameter(func)
    assert param is not None  # _commands only keeps functions that have one
    try:
        if param.kind is inspect.Parameter.KEYWORD_ONLY:
            result = func(**{param.name: args.text})
        else:
            result = func(args.text)
    except ValueError as exc:
        print(f"textkit: error: {exc}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
