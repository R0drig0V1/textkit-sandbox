"""Errors of the template engine ``textkit.template`` (plan task T3.4).

Both classes are importable from the package (``from textkit.template import TemplateError``)
but are not in its ``__all__``: ``__all__`` lists functions only (phase 3 rule "Packages").

They subclass ``ValueError`` because ``textkit.errors`` (plan task T3.2) is not merged yet
(phase 3 rule "Errors"); when it is, the base class becomes ``InvalidValueError``.
"""


class TemplateError(ValueError):
    """A template that cannot be rendered with the given context.

    Attributes:
        message: what went wrong, without the position.
        line: line of the offending tag, from 1. A line ends after each ``"\\n"`` only, so a
            ``"\\r"`` does not start a new line.
        column: column of the opening delimiter (``{{``, ``{%`` or ``{#``) of the offending
            tag, from 1, counted in code points (a ``"\\r"`` is a column).

    ``str(error)`` is ``"<line>:<column>: <message>"``, the form the ``render`` subcommand
    prints.
    """

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"{line}:{column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class TemplateSyntaxError(TemplateError):
    """A template that cannot be parsed: raised before anything is rendered.

    Raised for an unterminated ``{{``, ``{%`` or ``{#``; a block with no end tag; an unknown
    tag or filter; a bad filter argument; ``else``, ``endif`` or ``endfor`` without their
    opening tag; and malformed tags and expressions. See ``docs/template.md``.
    """
