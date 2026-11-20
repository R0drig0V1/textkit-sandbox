"""Registry of the tool subcommands of ``python3 -m textkit`` (plan task T3.1).

A tool (a package ``textkit/<tool>/``) adds its subcommand as one module
``textkit/cli/<name>.py`` that builds a :class:`Command` and passes it to :func:`register` at
import time; ``textkit/cli/main.py`` finds and imports those modules with ``pkgutil`` and
asks :func:`commands` for the result. No shared file lists the tools, so two tools added in
parallel never touch the same line.

Tool names and function-command names (``textkit/cli/functions.py``) share one namespace.
This module cannot see the function commands, so ``_main`` checks that clash after
discovery; :func:`register` only checks tools against tools.

The registry is process-wide state (a module-level dict). Tests that register fake commands
snapshot ``_REGISTRY`` and restore it (``tests/test_cli_registry.py``).
"""

import argparse
from dataclasses import dataclass
from typing import Callable, Dict, List

# The program name every message of the command line starts with. A tool builds its error
# prefix from it, "python3 -m textkit <name>: error: ...", as argparse does for usage errors.
PROG = "python3 -m textkit"


@dataclass(frozen=True)
class Command:
    """One tool subcommand: ``python3 -m textkit <name> ...``.

    ``name`` is the subcommand (by convention the module name, ``textkit/cli/<name>.py``);
    ``summary`` is one line, shown under ``tools:`` in ``--help`` and as the subcommand's
    description. ``configure`` adds the subcommand's arguments to the parser ``_main`` creates
    for it (it must not use the ``dest`` ``command``, which holds the subcommand name).
    ``run`` receives the whole parsed namespace and returns the exit code, which ``_main``
    returns as is: a tool handles its own errors and never relies on ``_main`` to catch them.
    """

    name: str
    summary: str
    configure: Callable[[argparse.ArgumentParser], None]
    run: Callable[[argparse.Namespace], int]


# name -> command. Private: tools go through register(), readers through commands().
_REGISTRY: Dict[str, Command] = {}


def register(command: Command) -> Command:
    """Add ``command`` to the registry and return it (usable as ``X = register(Command(...))``).

    Registering the same ``Command`` object again is a no-op, so importing a tool module
    twice by different routes does no harm. Raises ``RuntimeError`` when a *different*
    command already has that name: keeping either one silently would make the other
    unreachable, so every run fails instead.
    """
    existing = _REGISTRY.get(command.name)
    if existing is command:
        return command
    if existing is not None:
        raise RuntimeError(
            f"tool command {command.name!r} is registered twice: "
            f"{existing!r} and {command!r}"
        )
    _REGISTRY[command.name] = command
    return command


def commands() -> List[Command]:
    """Return every registered command, sorted by name (a new list; the registry is not exposed)."""
    return [_REGISTRY[name] for name in sorted(_REGISTRY)]
