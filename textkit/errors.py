"""The exceptions textkit raises for a rejected input (plan task T3.2).

- ``TextkitError`` is the base of every exception textkit defines. A caller that wants to
  handle "textkit said no" catches it, and only it.
- ``InvalidValueError`` is raised by a function that rejects an argument's value (a width
  below the minimum, a negative length, ...). An argument of the wrong *type* still raises the
  built-in ``TypeError``.

``InvalidValueError`` deliberately does **not** inherit from ``ValueError`` (ADR
``docs/decisions/0006-invalid-value-error-not-a-value-error.md``): a ``ValueError`` that
escapes textkit is then a bug in textkit, never a rejected input, and ``except TextkitError``
cannot swallow it by accident. The exception classes of the phase 3 tools subclass
``InvalidValueError`` (phase 3 rule "Errors"); ``tests/test_errors.py`` enforces both rules.

This module defines classes only: it has no public functions, so no README row and no
command-line command.
"""


class TextkitError(Exception):
    """Base class of every exception textkit defines.

    Catch this to handle any input textkit rejects. It is never raised directly.
    """


class InvalidValueError(TextkitError):
    """An argument has the right type but a value the function rejects.

    The message names the parameter and the value, for example
    ``"width must be at least 1, got 0"``. Not a ``ValueError``: see the module docstring.
    """
