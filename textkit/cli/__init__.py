"""The command line of textkit, ``python3 -m textkit`` (plan tasks T2.6, T2.7, T3.1).

Modules:

- ``main.py``: ``_main``, the argument parser and ``--version``; ``textkit/__main__.py``
  only calls ``_main``.
- ``functions.py``: the function commands, ``python3 -m textkit <function> <text>``,
  discovered from textkit's public functions (T2.6).
- ``registry.py``: ``Command``, ``register``, ``commands`` and ``PROG``, for the tool
  subcommands.
- any other module ``<name>.py`` (whose name does not start with ``_``): one tool
  subcommand, ``python3 -m textkit <name> ...``, which registers a ``Command`` when it is
  imported. ``main._load_tools`` finds these modules with ``pkgutil``; nothing lists them by
  hand, so adding a tool never edits a shared file.

The package has no public functions: ``__all__`` is empty, so ``scripts/check.sh`` and
``tests/test_api.py`` ask for no README row. Importing it imports nothing else.
"""

__all__ = []
