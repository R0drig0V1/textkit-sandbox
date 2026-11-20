"""Function commands of the command line: ``python3 -m textkit <function> <text>`` (T2.6).

The commands discovered from textkit's public functions, exactly as plan task T2.6 defines
them; ``textkit/cli/main.py`` builds the parser and runs them (plan task T3.1 moved this code
out of ``textkit/__main__.py`` unchanged). The commands are discovered at run time, never
hard-coded, so a public function added to any module later becomes a command with no change
here. A command is a *public function* (the definition in the phase 1 "Rules for every task":
a top-level ``def`` whose name does not start with ``_``, in a module of ``textkit/`` whose
name does not start with ``_``) that has exactly one parameter without a default; parameters
with defaults keep their default.

Every top-level name in this file starts with ``_``: ``textkit/cli/`` has no public functions
(its ``__all__`` is empty), and the names say so to a reader too.
"""

import importlib
import inspect
import json
import pkgutil
from types import ModuleType
from typing import Any, Callable, Iterable, List

import textkit


def _textkit_modules() -> List[ModuleType]:
    """Import and return every public module of the ``textkit`` package, sorted by name.

    Modules whose name starts with ``_`` (``__main__``, ``_tokens``, ...) and subpackages
    (``cli`` itself, the tool packages) are skipped, matching the public-function definition
    and ``scripts/check.sh``: a tool package gets its subcommand from ``textkit/cli/``
    instead. An import error in a module propagates: a broken module is a bug, not something
    to hide.
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
