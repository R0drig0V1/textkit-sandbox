"""Lexer of ``textkit.template``: splits a template into text and tag tokens (plan task T3.4).

A template is text with three kinds of tags, each found by its opening delimiter and closed
by the first matching closing delimiter after it:

- ``{{ ... }}``, an output tag: token kind ``VAR``;
- ``{% ... %}``, a block tag (``if``, ``else``, ``endif``, ``for``, ``endfor``): kind
  ``BLOCK``;
- ``{# ... #}``, a comment: dropped here, so the parser never sees it.

Everything else is ``TEXT``, copied as is (``"\\r\\n"`` included). The lexer does not look
inside tags beyond stripping the whitespace around their content; the parser gives that
content a meaning. Every token carries the line and column of its first character (for a tag,
its opening delimiter), which is where every error about that tag is reported.
"""

import re
from typing import List, NamedTuple, Tuple

from textkit.template.exceptions import TemplateSyntaxError

TEXT = "text"
VAR = "var"
BLOCK = "block"

# Any opening delimiter. A lone "{" (or "{" followed by anything else) is plain text.
_OPENER = re.compile(r"\{[{%#]")
_CLOSER = {"{{": "}}", "{%": "%}", "{#": "#}"}
_KIND = {"{{": VAR, "{%": BLOCK}


class Token(NamedTuple):
    """One piece of a template.

    ``kind`` is ``TEXT``, ``VAR`` or ``BLOCK``. ``value`` is the text itself for ``TEXT``,
    and for a tag the content between its delimiters with surrounding whitespace stripped
    (``"{{  x }}"`` -> ``"x"``). ``line`` and ``column`` (both from 1) locate the token's
    first character.
    """

    kind: str
    value: str
    line: int
    column: int


class _Lines:
    """Turns offsets into (line, column) pairs, for offsets that never decrease.

    Lines end after each ``"\\n"`` only (a ``"\\r"`` is an ordinary column), and columns
    count code points. Moving forward counts only the newlines in between, so lexing stays
    linear in the size of the template.
    """

    def __init__(self, template: str) -> None:
        self._template = template
        self._offset = 0
        self._line = 1
        self._line_start = 0

    def at(self, offset: int) -> Tuple[int, int]:
        """Return the (line, column) of ``offset``; ``offset`` must not go backwards."""
        newlines = self._template.count("\n", self._offset, offset)
        if newlines:
            self._line += newlines
            self._line_start = self._template.rfind("\n", self._offset, offset) + 1
        self._offset = offset
        return self._line, offset - self._line_start + 1


def position(template: str, offset: int) -> Tuple[int, int]:
    """Return the (line, column) of ``offset`` in ``template``, both from 1.

    A line ends after each ``"\\n"`` only, so ``"\\r"`` and ``"\\r\\n"``'s ``"\\r"`` count
    as columns; columns are code points (``len``). ``offset`` may equal ``len(template)``.

    Raises:
        IndexError: if ``offset`` is negative or greater than ``len(template)``.
    """
    if not 0 <= offset <= len(template):
        raise IndexError(f"offset {offset} is outside the template (length {len(template)})")
    return _Lines(template).at(offset)


def tokenize(template: str) -> List[Token]:
    """Split ``template`` into ``TEXT``, ``VAR`` and ``BLOCK`` tokens, in order.

    Comments (``{# ... #}``) produce no token. A tag ends at the first closing delimiter of
    its own kind after the opening one, so ``{{ a %} }}`` is the output tag ``"a %}"``
    (which the parser then rejects). Text between tags is never empty: no ``TEXT`` token
    has ``value == ""``.

    Raises:
        TemplateSyntaxError: for an unterminated ``{{``, ``{%`` or ``{#``, at the position
            of that opening delimiter.
    """
    tokens: List[Token] = []
    lines = _Lines(template)
    pos = 0
    while True:
        match = _OPENER.search(template, pos)
        start = match.start() if match else len(template)
        if start > pos:
            tokens.append(Token(TEXT, template[pos:start], *lines.at(pos)))
        if match is None:
            return tokens
        opener = match.group()
        closer = _CLOSER[opener]
        end = template.find(closer, start + 2)
        line, column = lines.at(start)
        if end < 0:
            raise TemplateSyntaxError(
                f"unterminated {opener!r}: no {closer!r} after it", line, column
            )
        if opener in _KIND:
            tokens.append(Token(_KIND[opener], template[start + 2 : end].strip(), line, column))
        pos = end + 2
