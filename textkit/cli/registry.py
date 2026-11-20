"""The registry of tool subcommands of ``python3 -m textkit`` (plan task T3.1).

A tool adds a subcommand by writing one module ``textkit/cli/<name>.py`` that calls
``register(Command(...))`` at import time; ``textkit.cli.main._load_tools`` imports every
module of ``textkit/cli/``, so no shared file lists the tools. ``_main`` then adds one
sub-parser per registered command, lets ``configure`` add its arguments and hands the parsed
namespace to ``run``, whose return value is the exit code.

The registry is process-wide state (``_REGISTRY``). Tests that change it snapshot it in
``setUp`` and restore it in ``tearDown`` (see ``tests/test_cli_registry.py``).
"""

import argparse
from dataclasses import dataclass
from typing import Callable, Dict

# The program name in usage lines and error messages, for example
# "python3 -m textkit render: error: <path>: <reason>" (phase 3 rule "The command line").
PROG = "python3 -m textkit"


@dataclass(frozen=True)
class Command:
    """One tool subcommand.

    ``name`` is the subcommand (``python3 -m textkit <name> ...``); ``summary`` is one line,
    shown under ``tools:`` in ``--help`` and as the subcommand's description;
    ``configure`` adds the subcommand's arguments to its parser; ``run`` receives the whole
    parsed namespace, handles its own errors and returns the exit code.
    """

    name: str
    summary: str
    configure: Callable[[argparse.ArgumentParser], None]
    run: Callable[[argparse.Namespace], int]


# Name -> command. Private: tools go through register(), the command line through commands().
_REGISTRY: Dict[str, Command] = {}


def register(command: Command) -> Command:
    """Add ``command`` to the registry and return it (so it can be kept in a module name).

    Registering the same ``Command`` object again is a no-op, so importing a tool module
    twice is harmless. Raises ``RuntimeError`` when a different command already has the
    same name: keeping either silently would make the other unreachable. A clash with a
    function command is not checked here (the functions are discovered later); ``_main``
    checks it on every run.
    """
    existing = _REGISTRY.get(command.name)
    if existing is command:
        return command
    if existing is not None:
        raise RuntimeError(f"two different tool commands are named {command.name!r}")
    _REGISTRY[command.name] = command
    return command


def commands() -> list[Command]:
    """Return the registered commands, sorted by name."""
    return [_REGISTRY[name] for name in sorted(_REGISTRY)]
