"""The exceptions textkit raises on purpose (plan task T3.2, ADR 0006).

- ``TextkitError``: the base class of every error textkit raises on purpose. Catch it to
  handle any input textkit rejects; the command line (``textkit/cli/main.py``) does.
- ``InvalidValueError(TextkitError)``: an argument has the right type but a value the
  function does not accept (``truncate("x", 2)``: a width below the suffix length). A
  function documents it under "Raises:" with the condition.

``InvalidValueError`` is deliberately **not** a ``ValueError``: a ``ValueError`` that escapes
textkit is then a bug in textkit (an unchecked standard-library call), never a rejected input,
and ``except TextkitError`` does not hide it. See ADR 0006,
``docs/decisions/0006-error-hierarchy.md``. An argument of the wrong type still
raises the built-in ``TypeError``: that is a bug in the caller, not a value to handle.

Tool packages define their own exception classes next to their code (a template syntax error,
a patch that does not apply); they subclass ``InvalidValueError`` (phase 3 rule "Errors"), so
``except TextkitError`` catches them too. ``tests/test_errors.py`` checks that every exception
class defined in ``textkit/`` is a ``TextkitError`` and that no code under ``textkit/`` raises,
builds or subclasses ``ValueError``.

This module defines classes only: it has no public functions and no README row.
"""


class TextkitError(Exception):
    """Base class of every error textkit raises on purpose.

    Never raised directly: textkit raises a subclass that says what went wrong. Catch this
    class to handle any rejected input without also catching textkit's bugs.
    """


class InvalidValueError(TextkitError):
    """An argument has an accepted type but a value the function rejects.

    The message names the argument, the value and the rule (``"width must be at least 1,
    got 0"``). Not a subclass of ``ValueError``: see this module's docstring.
    """
