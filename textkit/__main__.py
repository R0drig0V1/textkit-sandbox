"""Entry point of ``python3 -m textkit``: runs ``textkit.cli.main._main`` (plan task T3.1).

The command line itself lives in the package ``textkit/cli/``. This private module holds no
public functions (``scripts/check.sh`` and ``tests/test_api.py`` skip it).
"""

import sys

from textkit.cli.main import _main

if __name__ == "__main__":
    sys.exit(_main())
