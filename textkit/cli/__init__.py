"""The ``python3 -m textkit`` command line, as a package (plan task T3.1).

- ``registry.py``: ``Command``, ``register``, ``commands`` and ``PROG``, the interface a tool
  uses to add a subcommand.
- ``functions.py``: the commands discovered at run time from the public functions of the
  single-file modules of ``textkit/`` (plan task T2.6).
- ``main.py``: ``_main``, the parser, ``--version`` and ``_load_tools``.
- ``<name>.py``: one module per tool subcommand, written by the tool's own task; it calls
  ``registry.register`` when imported. ``main._load_tools`` finds these modules with
  ``pkgutil``, so adding a tool edits no shared file.

``__all__`` is empty: the package has no public functions, so ``scripts/check.sh`` and
``tests/test_api.py`` ask for no README row or CHANGELOG line for anything in it.
"""

__all__ = []
