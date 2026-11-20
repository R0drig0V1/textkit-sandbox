"""Lexer of the template engine (plan task T3.4): template text -> a flat list of tokens.

The lexer only finds the tags; it does not look inside them. A tag starts at ``{{``
(output), ``{%`` (block tag) or ``{#`` (comment) and ends at the first matching closer
(``}}``, ``%}``, ``#}``) after it; there are no string literals in the syntax, so no closer
can be hidden inside one. Everything between tags is text, copied as is (a lone ``{`` or
``}}`` included). Comments are dropped here, so the parser never sees them.

Positions follow ``docs/template.md``: ``line`` and ``column`` count from 1, columns in code
points, and a line ends after each ``"\\n"`` only (a ``"\\r"`` is one more column).
"""

import re
from typing import List, NamedTuple

from textkit.template.errors import TemplateSyntaxError

TEXT = "text"
OUTPUT = "output"
BLOCK = "block"

# Opening delimiter -> (token kind, closing delimiter). A kind of None marks a comment,
# which produces no token.
_DELIMITERS = {"{{": (OUTPUT, "}}"), "{%": (BLOCK, "%}"), "{#": (None, "#}")}

# Any opening delimiter. Searching for all three at once finds the earliest tag.
_OPENER = re.compile(r"\{[{%#]")


class Token(NamedTuple):
    """One piece of a template.

    ``kind`` is ``TEXT``, ``OUTPUT`` or ``BLOCK``. For ``TEXT``, ``value`` is the text exactly
    as written; for the other two it is what lies between the delimiters, with surrounding
    whitespace stripped (so ``{{x}}`` and ``{{ x }}`` give the same token). ``line`` and
    ``column`` are those of the token's first character: the opening delimiter of a tag.
    """

    kind: str
    value: str
    line: int
    column: int


def _advance(line: int, column: int, chunk: str) -> tuple[int, int]:
    """Return the position just after ``chunk``, which starts at ``(line, column)``.

    Only ``"\\n"`` starts a new line; ``"\\r"`` and every other character is one column.
    """
    newlines = chunk.count("\n")
    if not newlines:
        return line, column + len(chunk)
    # The new column is the number of characters after the last newline, plus 1.
    return line + newlines, len(chunk) - chunk.rfind("\n")


def tokenize(template: str) -> List[Token]:
    """Split ``template`` into ``TEXT``, ``OUTPUT`` and ``BLOCK`` tokens, in order.

    Comments (``{# ... #}``) produce no token; the text on each side of one gives two
    ``TEXT`` tokens. ``""`` gives ``[]``. The content of tags is not checked here (the parser
    does that), so ``{{ }}`` is an ``OUTPUT`` token with value ``""``.

    Raises:
        TemplateSyntaxError: for a ``{{``, ``{%`` or ``{#`` with no closer after it, at the
            position of that opening delimiter.
    """
    tokens: List[Token] = []
    pos = 0
    line, column = 1, 1  # the position of template[pos]
    while True:
        match = _OPENER.search(template, pos)
        if match is None:
            if pos < len(template):
                tokens.append(Token(TEXT, template[pos:], line, column))
            return tokens
        start = match.start()
        if start > pos:
            text = template[pos:start]
            tokens.append(Token(TEXT, text, line, column))
            line, column = _advance(line, column, text)
        opener = match.group()
        kind, closer = _DELIMITERS[opener]
        # Search after the opener, so "{%}" is not closed by its own "%}".
        end = template.find(closer, start + len(opener))
        if end == -1:
            raise TemplateSyntaxError(
                f"{opener!r} is never closed with {closer!r}", line, column
            )
        if kind is not None:
            inner = template[start + len(opener) : end].strip()
            tokens.append(Token(kind, inner, line, column))
        pos = end + len(closer)
        line, column = _advance(line, column, template[start:pos])
