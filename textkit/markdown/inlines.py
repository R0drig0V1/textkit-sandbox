"""Inline Markdown of ``textkit.markdown``: emphasis, code spans, links and escapes.

``render_inlines(text)`` turns the text of one block (a heading, a paragraph, a list item, a
paragraph of a quote) into HTML. The constructs, in the order they are tried at each
position:

- a backslash before ``\\``, ``*``, ``\\```, ``[`` or ``]`` prints that character as is; a
  backslash before anything else is an ordinary character;
- ```code``` : a backtick, one or more characters other than a backtick, a backtick. The
  content is escaped and nothing else: a backslash inside is a character;
- ``[text](url)``: the text runs to the first ``]`` that is not escaped and not inside a code
  span, the URL from the ``(`` right after it to the next ``)``. The text is parsed as
  inlines; the URL goes through ``html.safe_url`` and is escaped;
- ``**strong**`` and ``*em*``: the opening marker is followed by a character that is not
  whitespace, and the closing one is the first matching marker after it that follows a
  character that is not whitespace (escapes, code spans and links are skipped while
  looking for it, and so is every ``**`` when looking for a single ``*``); a ``**`` closer
  is the last two stars of its run (``**a *b***``). The content is parsed as inlines, so
  the two nest.

Anything that does not complete one of these, an unmatched marker included, is printed as
is, escaped (``html.escape``): no input raises, and no raw HTML reaches the output.
"""

from typing import NamedTuple, Optional

from textkit.markdown.html import escape, safe_url

# The characters a backslash escapes. Others keep their backslash ("\_" prints "\_").
ESCAPABLE = "\\*`[]"


class _Link(NamedTuple):
    """A complete ``[text](url)``: ``text`` and ``url`` raw, ``end`` just past the ``)``."""

    text: str
    url: str
    end: int


def _is_space(char: str) -> bool:
    """Whether ``char`` counts as whitespace next to an emphasis marker."""
    return char.isspace()


def _code_span_end(text: str, start: int) -> Optional[int]:
    """Index of the backtick that closes a code span opened at ``start``, or ``None``.

    The span needs at least one character between its backticks, so ``"``"`` is two
    literal backticks rather than an empty span.
    """
    if start + 1 >= len(text) or text[start + 1] == "`":
        return None
    end = text.find("`", start + 1)
    return end if end != -1 else None


def _link_at(text: str, start: int) -> Optional[_Link]:
    """The link that starts with the ``[`` at ``start``, or ``None`` if there is none."""
    i = start + 1
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPABLE:
            i += 2
            continue
        if char == "`":
            end = _code_span_end(text, i)
            if end is not None:
                i = end + 1
                continue
        if char == "]":
            break
        i += 1
    else:
        return None
    # i is the closing bracket; the URL must follow it directly.
    if not text.startswith("(", i + 1):
        return None
    close = text.find(")", i + 2)
    if close == -1:
        return None
    return _Link(text=text[start + 1 : i], url=text[i + 2 : close], end=close + 1)


def _skip(text: str, i: int) -> int:
    """Index just past the escape, code span or link at ``i``, or ``i`` if none starts there.

    Used while looking for a closing emphasis marker, so a marker inside one of these
    (``*a `*` b*``, ``*see [x*y](u)*``) is not taken as the closer.
    """
    char = text[i]
    if char == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPABLE:
        return i + 2
    if char == "`":
        end = _code_span_end(text, i)
        if end is not None:
            return end + 1
    if char == "[":
        link = _link_at(text, i)
        if link is not None:
            return link.end
    return i


def _emphasis_end(text: str, start: int, width: int) -> Optional[int]:
    """Index of the marker that closes the ``width``-star opener at ``start``, or ``None``."""
    content = start + width
    if content >= len(text) or _is_space(text[content]):
        return None
    marker = "*" * width
    i = content
    while i < len(text):
        after = _skip(text, i)
        if after != i:
            i = after
            continue
        if text.startswith("**", i) and width == 1:
            # A "**" is never the closer of a single "*": it opens or closes a strong span.
            i += 2
            continue
        if text.startswith(marker, i) and i > content and not _is_space(text[i - 1]):
            if width == 1:
                return i
            # A "**" closer is the last two stars of its run, so the stars before them
            # close an emphasis inside: "**a *b***" is strong(a em(b)).
            run_end = i
            while run_end < len(text) and text[run_end] == "*":
                run_end += 1
            return run_end - 2
        i += 1
    return None


def render_inlines(text: str) -> str:
    """Render the inline Markdown in ``text`` as HTML, escaping everything else.

    ``text`` is the content of one block, its lines already joined by one space. Never
    raises for a ``str``; an unmatched marker (``"2 * 3"``, ``"[a]"``, ``"`x"``) is printed
    as is.
    """
    out = []
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPABLE:
            out.append(escape(text[i + 1]))
            i += 2
            continue
        if char == "`":
            end = _code_span_end(text, i)
            if end is not None:
                out.append(f"<code>{escape(text[i + 1 : end])}</code>")
                i = end + 1
                continue
        elif char == "[":
            link = _link_at(text, i)
            if link is not None:
                href = escape(safe_url(link.url))
                out.append(f'<a href="{href}">{render_inlines(link.text)}</a>')
                i = link.end
                continue
        elif char == "*":
            width = 2 if text.startswith("**", i) else 1
            end = _emphasis_end(text, i, width)
            if end is not None:
                tag = "strong" if width == 2 else "em"
                inner = render_inlines(text[i + width : end])
                out.append(f"<{tag}>{inner}</{tag}>")
                i = end + width
                continue
            # An unmatched "**" prints one "*" and the second is tried as an opener of its
            # own, so "**a*" gives "*<em>a</em>".
        out.append(escape(char))
        i += 1
    return "".join(out)
