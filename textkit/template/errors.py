"""Errors of the template engine (plan task T3.4).

Both classes carry the position of the offending tag: ``line`` and ``column``, counted from
1, columns in code points. A line ends after each ``"\\n"`` only, so a ``"\\r"`` is one more
column, not a line break (the rule is in ``docs/template.md``). The position is that of the
opening delimiter (``{{``, ``{%`` or ``{#``) of the tag at fault; for a block with no end tag,
that of the block's opening tag.

Until the error hierarchy of plan task T3.2 is merged, ``TemplateError`` subclasses
``ValueError`` (phase 3 rule "Errors"), so a caller that already catches textkit's
``ValueError`` catches template errors too. These classes are importable from
``textkit.template`` but are not in its ``__all__``, which lists functions only.
"""


class TemplateError(ValueError):
    """A template could not be rendered; ``line`` and ``column`` locate the tag at fault.

    Raised directly while rendering: a ``for`` over a value that is not a list, a dotted
    name through a value that is not a dict, and a name missing from the context outside an
    ``if`` (ADR "template missing names"). ``str(error)`` is ``"<line>:<column>: <message>"``
    and ``message`` holds the message alone.
    """

    def __init__(self, message: str, line: int, column: int) -> None:
        # args holds the constructor's arguments, so copy and pickle rebuild the error
        # (they call type(error)(*error.args)); __str__ formats them.
        super().__init__(message, line, column)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"{self.line}:{self.column}: {self.message}"


class TemplateSyntaxError(TemplateError):
    """The template text is not valid template syntax; raised while lexing and parsing.

    Raised for an unterminated ``{{``, ``{%`` or ``{#``; a block with no end tag; an unknown
    tag or filter; a malformed expression or tag; a bad filter argument (``truncate`` with
    no width, a non-integer width or a width below 3, or an argument to a filter that takes
    none); and ``else``, ``endif`` or ``endfor`` without their opening tag.
    """
