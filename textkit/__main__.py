"""Run the textkit command line: ``python3 -m textkit <command> ...`` (plan tasks T2.6, T3.1).

The command line lives in the package ``textkit/cli/`` (see its ``__init__.py``); this file
only calls it. Importing it has no side effects. Every top-level name starts with ``_``:
``__main__`` is a private module and holds no public functions.
"""

import sys

from textkit.cli.main import _main

if __name__ == "__main__":
    sys.exit(_main())
