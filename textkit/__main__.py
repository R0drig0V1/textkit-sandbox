"""Command line for textkit: ``python3 -m textkit <function> <text>``.

Runs one textkit function on one text and prints the result. ``python3 -m textkit --help``
lists the functions; ``python3 -m textkit <function> --help`` shows that function's full
docstring.

Which functions are commands
    The commands are found at run time, so a new helper shows up with no list to maintain.
    A function is a command when all of these hold:

    - it is defined (not just imported) in a public module of the package
      (``textkit/<name>.py`` with no leading ``_``; ``__main__`` and private modules such
      as ``_tokens`` are skipped). Checking the defining module keeps a helper that one
      module imports from another (``from textkit._tokens import char_class``) from
      appearing twice or under the wrong module;
    - its name has no leading ``_``;
    - it takes exactly one required parameter, positional and annotated ``str``; every
      other parameter has a default. So ``squeeze(text)`` is a command, but
      ``truncate(text, width, suffix="...")``, ``wrap(text, width)`` and
      ``slug_title(text, max_len)`` are not: their second parameter is required and the
      command line has no way to pass it. Optional parameters always take their defaults.

    Two commands with the same name in different modules raise ``RuntimeError`` while the
    commands are collected (on every run, and in ``tests/test_main.py``), naming both
    modules, instead of one silently hiding the other.

The text
    Exactly one argument after the function name, so text with spaces must be quoted
    (``python3 -m textkit slugify "Hello, World"``). Several words are not joined: joining
    would change the whitespace that functions like ``squeeze`` and ``word_count`` look
    at, so extra arguments are a usage error. The text ``-`` means "read the text from
    standard input"; one trailing line break (``\\n`` or ``\\r\\n``) is removed from it, so
    ``echo "some text" | python3 -m textkit slugify -`` gives the same result as passing
    ``"some text"``. Text that starts with ``-`` goes after ``--``
    (``python3 -m textkit squeeze -- "-x  y"``).

Output, by the type of the result
    - ``str``: printed as is, followed by a newline.
    - ``bool``: ``true`` or ``false`` (the exit code stays 0 either way; it only reports
      errors).
    - ``int``, ``float`` and anything else not listed: ``str(value)``.
    - ``list`` or ``tuple``: one item per line, in order; an empty list prints nothing.
    - ``dict``: one ``key<TAB>value`` line per entry, in the dict's order (for
      ``char_freq``, order of first appearance). A key or value that itself contains a tab
      or a newline makes the output ambiguous; no current command can produce one.

Exit codes
    - 0: success.
    - 1: the function raised ``ValueError`` or ``TypeError``, or standard input could not
      be decoded; the message goes to standard error as ``textkit: <function>: <message>``.
    - 2: usage error (argparse's convention): no function, an unknown function, a missing
      text or more than one text. Usage and the message go to standard error.

    No error path prints a traceback. Any other exception is a bug in textkit and is left
    to propagate.

The entry point is ``_main``, not ``main``: ``scripts/check.sh`` treats every public
top-level function in ``textkit/*.py`` as a text helper that needs a README table row and a
changelog entry, and the command line is not one. The parser is built by
``_build_parser`` so later options (``--version``, plan task T2.7) can be added there.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import pkgutil
import sys
from typing import Callable, Dict, Iterable, List, Optional

import textkit

Command = Callable[[str], object]

_STDIN = "-"

_EPILOG = """\
The text is one argument: quote text with spaces. "-" reads the text from standard input
(one trailing line break removed); put text that starts with "-" after "--".

Output: a str as is; a bool as true/false; a number as str(); a list one item per line;
a dict one "key<TAB>value" line per entry, in order.

Exit codes: 0 success; 1 the function rejected the text (ValueError/TypeError) or stdin
could not be decoded; 2 usage error (unknown function, missing or extra text).
"""


def _public_modules() -> List[str]:
    """Return the dotted names of textkit's public modules (no leading ``_``), sorted."""
    return sorted(
        f"{textkit.__name__}.{info.name}"
        for info in pkgutil.iter_modules(textkit.__path__)
        if not info.name.startswith("_")
    )


def _takes_one_text(func: Callable[..., object]) -> bool:
    """True if ``func`` has exactly one required parameter, positional and typed ``str``.

    Every other parameter must have a default (``*args`` and ``**kwargs`` count as
    optional). The annotation is accepted as the type ``str`` or, under
    ``from __future__ import annotations``, as the string ``"str"``.
    """
    try:
        params = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):  # no introspectable signature (some builtins)
        return False
    required = [
        p
        for p in params
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    if len(required) != 1:
        return False
    (param,) = required
    positional = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    return param.kind in positional and param.annotation in (str, "str")


def _discover(module_names: Optional[Iterable[str]] = None) -> Dict[str, Command]:
    """Collect the commands: public one-text functions defined in the given modules.

    ``module_names`` defaults to every public textkit module (``_public_modules``); tests
    pass their own. The result maps each function name to the function, sorted by name.

    Raises:
        RuntimeError: if two modules define a command with the same name. Both modules are
            named, so the clash is fixed at its source rather than one function shadowing
            the other.
    """
    if module_names is None:
        module_names = _public_modules()
    found: Dict[str, Command] = {}
    for module_name in module_names:
        module = importlib.import_module(module_name)
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Skip private names and functions imported from elsewhere.
            if name.startswith("_") or func.__module__ != module_name:
                continue
            if not _takes_one_text(func):
                continue
            if name in found:
                raise RuntimeError(
                    f"textkit command name clash: {name!r} is defined in both "
                    f"{found[name].__module__} and {module_name}"
                )
            found[name] = func
    return dict(sorted(found.items()))


def _build_parser(commands: Dict[str, Command]) -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per command, each taking one ``text``."""
    parser = argparse.ArgumentParser(
        prog="python3 -m textkit",
        description="Run one textkit function on one text and print the result.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="function", metavar="<function>", title="functions", required=True
    )
    for name, func in commands.items():
        doc = inspect.getdoc(func) or ""
        summary = doc.splitlines()[0] if doc else ""
        sub = subparsers.add_parser(
            name,
            help=summary,
            description=doc,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        sub.add_argument("text", help='the text (quote it if it has spaces; "-" reads stdin)')
    return parser


def _read_stdin() -> str:
    """Read all of standard input, minus one trailing ``\\n`` or ``\\r\\n``.

    Raises:
        UnicodeDecodeError: if standard input is not valid in its encoding.
    """
    text = sys.stdin.read()
    if text.endswith("\r\n"):
        return text[:-2]
    if text.endswith("\n"):
        return text[:-1]
    return text


def _format(result: object) -> List[str]:
    """Return the output lines for ``result``, following the rules of the module docstring."""
    # bool before int: bool is a subclass of int.
    if isinstance(result, bool):
        return ["true" if result else "false"]
    if isinstance(result, str):
        return [result]
    if isinstance(result, (list, tuple)):
        return [str(item) for item in result]
    if isinstance(result, dict):
        return [f"{key}\t{value}" for key, value in result.items()]
    return [str(result)]


def _main(argv: Optional[List[str]] = None, commands: Optional[Dict[str, Command]] = None) -> int:
    """Run the command line and return its exit code (0, 1 or 2; see the module docstring).

    Args:
        argv: The arguments after the program name; defaults to ``sys.argv[1:]``.
        commands: The commands to offer; defaults to ``_discover()``. Tests pass their own.

    Output goes to ``sys.stdout`` and errors to ``sys.stderr``, both looked up at call
    time so tests can capture them. ``--help`` returns 0 instead of exiting.

    Raises:
        RuntimeError: from ``_discover`` on a command name clash.
    """
    if commands is None:
        commands = _discover()
    parser = _build_parser(commands)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # --help (0) or a usage error (2), already printed
        return exc.code if isinstance(exc.code, int) else 2
    func = commands[args.function]
    try:
        text = _read_stdin() if args.text == _STDIN else args.text
        result = func(text)
    except (ValueError, TypeError) as exc:  # UnicodeDecodeError is a ValueError
        print(f"textkit: {args.function}: {exc}", file=sys.stderr)
        return 1
    for line in _format(result):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
