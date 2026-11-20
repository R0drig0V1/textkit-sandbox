"""Inline Markdown of ``textkit.markdown``: emphasis, code spans, links and escapes.

``render_inlines(text)`` turns the text of one block (a heading, a paragraph, a list item, a
paragraph of a quote) into HTML. The constructs:

- a backslash before ``\\``, ``*``, ``\\```, ``[`` or ``]`` prints that character as is; a
  backslash before anything else is an ordinary character;
- ```code``` : a backtick, one or more characters other than a backtick, a backtick. The
  content is escaped and nothing else: a backslash inside is a character;
- ``[text](url)``: a ``]`` closes the nearest ``[`` before it that is still open, and makes
  a link when ``(`` follows it directly; the URL runs from there to the next ``)``. The text
  is parsed as inlines (a link inside a link is not made: forming a link closes every ``[``
  before it); the URL goes through ``html.safe_url`` and is escaped. A ``]`` that makes no
  link prints as is, and so does its ``[``;
- ``**strong**`` and ``*em*``: a run of stars can open emphasis when the character after it
  is not whitespace, and close it when the character before it is not whitespace. Each run
  that can close is matched with the nearest open run before it: two stars from each when
  both have two left (``<strong>``), else one (``<em>``), repeated while both have stars
  left. Stars are used from the inner side of each run, so ``**a *b***`` is
  strong(a em(b)). Runs inside a link are matched only with each other. Stars left over
  print as is.

Anything that does not complete one of these, an unmatched marker included, is printed as
is, escaped (``html.escape``): no input raises, and no raw HTML reaches the output.

**One pass, no recursion.** The text is read once, left to right, into a list of output
pieces; star runs are kept as ``_Delimiter`` records and matched with a stack (the
delimiter-stack method of CommonMark), and a link only rewrites the piece of its ``[``. So
the time is about linear in the length of the text, whatever it holds (a run of ten
thousand ``*`` or ``[`` included), and nesting depth is unlimited: there is no recursion
for deep input to exhaust.
"""

from dataclasses import dataclass, field
from typing import Optional, Union

from textkit.markdown.html import escape, safe_url

# The characters a backslash escapes. Others keep their backslash ("\_" prints "\_").
ESCAPABLE = "\\*`[]"


@dataclass
class _Delimiter:
    """A run of stars: how many are left, and the tags matched on each side of it.

    ``closes`` holds the closing tags, innermost first (the order they were matched);
    ``opens`` the opening tags, innermost first too, so they are written reversed.
    """

    count: int
    can_open: bool
    can_close: bool
    closes: list[str] = field(default_factory=list)
    opens: list[str] = field(default_factory=list)

    def html(self) -> str:
        # Closing tags use the stars on the left of the run, opening tags those on the
        # right; the stars no match used stay in the middle as text.
        return "".join(self.closes) + "*" * self.count + "".join(reversed(self.opens))


def _code_span_end(text: str, start: int) -> Optional[int]:
    """Index of the backtick that closes a code span opened at ``start``, or ``None``.

    The span needs at least one character between its backticks, so ``"``"`` is two
    literal backticks rather than an empty span. Each call stops at the next backtick, so
    all the calls of one pass read the text about once.
    """
    if start + 1 >= len(text) or text[start + 1] == "`":
        return None
    end = text.find("`", start + 1)
    return end if end != -1 else None


def _match_emphasis(delimiters: list[_Delimiter]) -> None:
    """Match the star runs of ``delimiters`` (in text order) into strong and em tags.

    Each run is visited once and each match uses up stars, so this is linear in the number
    of runs and stars.
    """
    openers: list[_Delimiter] = []
    for run in delimiters:
        if run.can_close:
            while run.count and openers:
                opener = openers[-1]
                width = 2 if opener.count >= 2 and run.count >= 2 else 1
                tag = "strong" if width == 2 else "em"
                opener.opens.append(f"<{tag}>")
                run.closes.append(f"</{tag}>")
                opener.count -= width
                run.count -= width
                if not opener.count:
                    openers.pop()
        if run.count and run.can_open:
            openers.append(run)


def render_inlines(text: str) -> str:
    """Render the inline Markdown in ``text`` as HTML, escaping everything else.

    ``text`` is the content of one block, its lines already joined by one space. Never
    raises for a ``str``, however long or deeply nested; an unmatched marker (``"2 * 3"``,
    ``"[a]"``, ``"`x"``) is printed as is.
    """
    pieces: list[Union[str, _Delimiter]] = []
    delimiters: list[_Delimiter] = []
    # Open "[": the index of its piece, and how many delimiters came before it.
    brackets: list[tuple[int, int]] = []
    # No ")" exists at or after this index (learned from a failed search), so a later "]("
    # does not search again: without it, many "](" with no ")" would be quadratic.
    no_paren_from = len(text) + 1
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPABLE:
            pieces.append(escape(text[i + 1]))
            i += 2
        elif char == "`" and _code_span_end(text, i) is not None:
            end = _code_span_end(text, i)
            assert end is not None  # for type checkers: tested on the line above
            pieces.append(f"<code>{escape(text[i + 1 : end])}</code>")
            i = end + 1
        elif char == "*":
            end = i
            while end < len(text) and text[end] == "*":
                end += 1
            before = text[i - 1] if i else " "
            after = text[end] if end < len(text) else " "
            run = _Delimiter(end - i, can_open=not after.isspace(), can_close=not before.isspace())
            pieces.append(run)
            delimiters.append(run)
            i = end
        elif char == "[":
            brackets.append((len(pieces), len(delimiters)))
            pieces.append("[")
            i += 1
        elif char == "]" and brackets:
            piece, first = brackets.pop()
            close = -1
            if text.startswith("(", i + 1) and i + 2 < no_paren_from:
                close = text.find(")", i + 2)
                if close == -1:
                    no_paren_from = i + 2
            if close == -1:
                # Not a link: the "[" (already a "[" piece) and this "]" print as is.
                pieces.append("]")
                i += 1
                continue
            # The stars inside the link text match only each other, then are done.
            _match_emphasis(delimiters[first:])
            del delimiters[first:]
            pieces[piece] = f'<a href="{escape(safe_url(text[i + 2 : close]))}">'
            pieces.append("</a>")
            # No link inside a link: the "[" still open before this one stay text.
            brackets.clear()
            i = close + 1
        else:
            pieces.append(escape(char))
            i += 1
    _match_emphasis(delimiters)
    return "".join(p if isinstance(p, str) else p.html() for p in pieces)
