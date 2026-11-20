"""Command line of textkit: ``python3 -m textkit <function> <text>`` (plan task T2.6).

Prints the result of one public function of textkit applied to one text argument, and lists
the available functions with ``--help``; ``--version`` prints ``textkit <version>`` from
``textkit.__version__`` (plan task T2.7) and exits 0. The commands are discovered at run time, never
hard-coded, so a public function added to any module later becomes a command with no change
here. A command is a *public function* (the definition in the phase 1 "Rules for every task":
a top-level ``def`` whose name does not start with ``_``, in a module of ``textkit/`` whose
name does not start with ``_``) that has exactly one parameter without a default; parameters
with defaults keep their default.

Every top-level name in this file starts with ``_``: ``__main__`` is a private module and
holds no public functions (``scripts/check.sh`` would otherwise ask for README rows).
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import sys
from types import ModuleType
from typing import Any, Callable, Iterable, List, Optional

import textkit

_PROG = "python3 -m textkit"


def _textkit_modules() -> List[ModuleType]:
    """Import and return every public module of the ``textkit`` package, sorted by name.

    Modules whose name starts with ``_`` (``__main__``, ``_tokens``, ...) and subpackages are
    skipped, matching the public-function definition and ``scripts/check.sh``. An import error
    in a module propagates: a broken module is a bug, not something to hide.
    """
    names = sorted(
        info.name
        for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_") and not info.ispkg
    )
    return [importlib.import_module(f"{textkit.__name__}.{name}") for name in names]


def _required_parameters(func: Callable[..., Any]) -> List[inspect.Parameter]:
    """Return the parameters of ``func`` that have no default.

    ``*args`` and ``**kwargs`` are not counted: they are never required.
    """
    variadic = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    return [
        p
        for p in inspect.signature(func).parameters.values()
        if p.kind not in variadic and p.default is inspect.Parameter.empty
    ]


def _commands(modules: Iterable[ModuleType]) -> dict[str, Callable[..., Any]]:
    """Map command name to function for every command found in ``modules``.

    A command is a function of the module (``f.__module__`` is the module itself, so names
    imported from elsewhere are ignored) whose name does not start with ``_`` and that has
    exactly one parameter without a default. The command name is the function name; the
    result is sorted by it.

    Raises ``RuntimeError`` when two modules define a command with the same name: picking one
    silently would make the other unreachable, so the test suite turns red instead.
    """
    found: dict[str, Callable[..., Any]] = {}
    for module in modules:
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            if len(_required_parameters(func)) != 1:
                continue
            if name in found:
                raise RuntimeError(
                    f"command {name!r} is defined in both {found[name].__module__} "
                    f"and {module.__name__}"
                )
            found[name] = func
    return dict(sorted(found.items()))


def _summary(func: Callable[..., Any]) -> str:
    """Return the first line of the docstring of ``func``, or ``""`` when it has none."""
    doc = inspect.getdoc(func)
    return doc.splitlines()[0].strip() if doc else ""


def _call(func: Callable[..., Any], text: str) -> Any:
    """Call ``func`` with ``text`` bound to its only parameter without a default.

    The argument is passed by name unless the parameter is positional-only, so a required
    keyword-only parameter works too; every other parameter keeps its default.
    """
    (param,) = _required_parameters(func)
    if param.kind is inspect.Parameter.POSITIONAL_ONLY:
        return func(text)
    return func(**{param.name: text})


def _format(result: Any) -> str:
    """Render a command result for printing.

    ``dict`` and ``list`` become ``json.dumps(result, ensure_ascii=False, sort_keys=True)``;
    anything else (``str`` as is, ``bool`` and ``int`` as ``print()`` shows them) goes
    through ``str``.
    """
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    return str(result)


def _parser(commands: dict[str, Callable[..., Any]]) -> argparse.ArgumentParser:
    """Build the argument parser: one sub-command per command, each taking one ``text``.

    The command list in ``--help`` is written by hand into the description (one
    ``name  first docstring line`` row per command under ``commands:``) rather than left to
    argparse, whose layout of sub-command help changes between Python versions and wraps
    long lines; a fixed layout is also what ``tests/test_cli.py`` parses.
    """
    width = max((len(name) for name in commands), default=0) + 2
    rows = "\n".join(f"  {name:<{width}}{_summary(func)}" for name, func in commands.items())
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=(
            "Run one textkit function on one text argument and print the result.\n\n"
            f"commands:\n{rows}"
        ),
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
        metavar="<function>",
        help="one of the commands listed above",
    )
    for name, func in commands.items():
        command = sub.add_parser(name, description=_summary(func))
        command.add_argument("text", help="the text argument (quote it)")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    """Run the command line on ``argv`` (``sys.argv[1:]`` when ``None``); return the exit code.

    Exit codes: 0 on success (and for ``--help`` and ``--version``); 2 on an unknown function, a wrong
    argument count or no arguments at all, with the usage and message on stderr (argparse's
    own handling, so ``_main`` returns the code instead of raising ``SystemExit``); 1 when the
    function raises ``ValueError`` for the given text, with the message on stderr.
    """
    commands = _commands(_textkit_modules())
    parser = _parser(commands)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 after --help and 2 on a usage error; report it as a return value.
        return exc.code if isinstance(exc.code, int) else 2
    try:
        result = _call(commands[args.command], args.text)
    except ValueError as exc:
        print(f"{_PROG} {args.command}: error: {exc}", file=sys.stderr)
        return 1
    print(_format(result))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
