<!-- ADR 0006: textkit's own error hierarchy, and why InvalidValueError is not a ValueError
     (plan task T3.2). -->
# 0006. Rejected values raise `InvalidValueError`, which is not a `ValueError`

## Context

In phases 1 and 2 a function that rejected an argument's value (`truncate` with a width
below the suffix length, `wrap` with `width < 1`, `slug_title` with `max_len < 0`,
`reading_time` with `wpm < 1`) raised the built-in `ValueError`, and `python3 -m textkit`
turned any `ValueError` from a function command into exit 1.

Phase 3 adds tools (a template engine, a Markdown converter, a line diff) that parse their
input and call the standard library, which raises `ValueError` for its own reasons
(`int("x")`, `json.loads`, `str.index`). With `ValueError` as textkit's error, a caller
cannot tell "textkit rejected my input" from "textkit hit a bug": `except ValueError` catches
both, and the command line printed a bug as if it were a user error, with no traceback.

Plan task T3.2 adds `textkit/errors.py`. The options for its base class were:

1. **`InvalidValueError(TextkitError, ValueError)`**: existing `except ValueError` code keeps
   working. But `except ValueError` still mixes rejected input with bugs, and
   `except TextkitError` would be optional, so nothing pushes callers to the precise form.
2. **`InvalidValueError(TextkitError)`, with `TextkitError(Exception)`**: textkit's errors
   form their own tree. Callers catch `TextkitError`; a `ValueError` that escapes textkit is
   then, by definition, a bug.
3. **Keep the built-in `ValueError`** and add nothing: no change, and no way to separate
   the two cases.

## Decision

Option 2. `textkit/errors.py` defines `TextkitError(Exception)`, the base of every exception
textkit defines, and `InvalidValueError(TextkitError)`, raised with the same messages as
before wherever textkit used to raise `ValueError`.

- `InvalidValueError` is **not** a `ValueError`. Callers catch `TextkitError` (or
  `InvalidValueError`).
- A **wrong type** still raises the built-in `TypeError` (`reading_time("x", 1.5)`): that
  is a programming error, not a rejected value, and Python's convention fits it.
- The **exception classes of the phase 3 tools** (`TemplateError`, `PatchError`, ...)
  subclass `InvalidValueError`, so `except TextkitError` covers them too.
- A `ValueError` from the **standard library** inside textkit never escapes: the code that
  can trigger it catches it and raises its own error (`raise ... from exc`, so the cause
  stays in the traceback).
- **`python3 -m textkit`** catches `TextkitError` around function commands (exit 1, the
  message on stderr, no traceback). Any other exception, a plain `ValueError` included,
  propagates with its traceback. Tools still handle their own errors in `Command.run`.

## Consequences

- **Breaking change** for callers that wrote `except ValueError` around a textkit call:
  the exception now passes through. They change it to `except TextkitError`. textkit has
  not been released yet (everything is under `## Unreleased`), so no published version
  changes behaviour.
- A `ValueError` traceback from textkit is a bug report, not a user error: the command line
  shows it in full instead of hiding it behind exit 1.
- `tests/test_errors.py` keeps the rule true. It scans every `*.py` under `textkit/` with
  `ast` (subpackages included) for `raise ValueError`, `ValueError(...)` and classes based on
  `ValueError`, and it imports every module `pkgutil.walk_packages` finds and checks that
  each exception class defined there is a `TextkitError` and not a `ValueError`. Code written
  before this decision and merged after it fails that test until it is converted (phase 3
  rule "Errors": whichever task merges second converts).
- Adding a new error kind means subclassing `InvalidValueError` (a rejected input) or
  `TextkitError` directly (if textkit ever needs an error that is not about an input); the
  runtime test accepts both.
