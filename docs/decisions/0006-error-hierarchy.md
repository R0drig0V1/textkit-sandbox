<!-- ADR 0006: textkit's own exception hierarchy, textkit.errors (plan task T3.2). -->
# 0006. `InvalidValueError` is a `TextkitError`, not a `ValueError`

## Context

In phases 1 and 2 a function rejected a bad value with the built-in `ValueError`
(`truncate("x", 2)`, `wrap(text, 0)`, `reading_time(text, 0)`, `slug_title(text, -1)`), and
the command line caught `ValueError` around function commands to exit 1 with the message.
Phase 3 adds tools built on more of the standard library (`int(...)`, `json.loads`, parsing),
which raise `ValueError` themselves when textkit passes them something it did not check.
With one exception type for both, a caller, and the command line, could not tell "textkit
rejected my input" from "textkit has a bug": `except ValueError` caught both, and the
command line turned a bug into a tidy one-line error with exit 1 and no traceback.

The options were:

1. **Keep `ValueError`.** Nothing changes for callers, and the two cases stay mixed.
2. **`InvalidValueError(TextkitError, ValueError)`**: textkit's own class that is also a
   `ValueError`. Existing `except ValueError` keeps working, but it still catches stray
   standard-library errors, and the command line, catching `TextkitError`, would behave
   differently from callers who catch `ValueError`.
3. **`InvalidValueError(TextkitError)`, not a `ValueError`**: textkit's errors and
   everything else are disjoint.

## Decision

Option 3. `textkit/errors.py` defines `TextkitError(Exception)`, the base of every error
textkit raises on purpose, and `InvalidValueError(TextkitError)` for an argument whose type
is accepted but whose value is not. Every `raise ValueError` in `textkit/` became
`raise InvalidValueError` with the same message. The exception classes of the tool packages
(phase 3) subclass `InvalidValueError`, so `except TextkitError` catches them too.

- **Callers catch `TextkitError`** (or a subclass) to handle rejected input.
- **A `ValueError` that escapes textkit is a bug**: textkit called the standard library
  without checking its input first. The phase 3 rule "Errors" requires every such
  `ValueError` to be caught inside textkit and turned into the task's own error, so none is
  ever part of the interface.
- **The command line catches `TextkitError`**, not `ValueError`, around function commands:
  a rejected input exits 1 with the message on stderr and no traceback; any other exception,
  a plain `ValueError` included, propagates with its traceback, so a bug is reported as one.
- **`TypeError` stays** for an argument of the wrong type (`reading_time("x", 2.0)`): that
  is a mistake in the calling code, not a value a program should handle, and it is the
  built-in convention.

## Consequences

- Breaking for callers: code that caught `ValueError` from textkit no longer catches its
  errors and must catch `TextkitError` (or `InvalidValueError`) instead. textkit is
  unreleased (`0.1.0`, everything under `## Unreleased`), so the cost is the change itself.
- The messages did not change, only the class; a doctest shows the new class name
  (`textkit.errors.InvalidValueError: ...`).
- `tests/test_errors.py` keeps the rule from eroding: it parses every module under
  `textkit/` (subpackages included) and fails on any `raise ValueError`, any
  `ValueError(...)` call and any class that subclasses `ValueError`, and it imports every
  module and checks that every exception class defined there is a `TextkitError`. A task
  that adds an error class or a `raise` cannot reintroduce `ValueError` without that test
  failing.
- Standard-library calls that can raise `ValueError` need a `try`/`except ValueError` that
  raises textkit's own error `from` it. That is more code per call, and it is the point: each
  such place is a decision about what the user is told.
