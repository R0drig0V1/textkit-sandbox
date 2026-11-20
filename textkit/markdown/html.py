"""HTML output of the Markdown subset, and ``to_html``, its public function (plan task T3.5).

Two safety rules hold for every byte this module writes (decided, with their reasons, in
docs/decisions/0009-markdown-subset-raw-html-and-link-schemes.md):

- raw HTML is never passed through: ``&``, ``<``, ``>`` and ``"`` are escaped in text, in
  code and in attribute values (``escape``);
- a link URL with a scheme other than ``http``, ``https`` or ``mailto`` becomes ``#``
  (``safe_url``), so ``javascript:`` and ``data:`` links cannot run anything.

The layout is fixed: each block starts on a line of its own; ``<ul>``/``<ol>``, every
``<li>`` and the closing tag, and ``<blockquote>``, every ``<p>`` and the closing tag, each
take one line; every line ends in ``"\\n"`` and no other whitespace is added.

Every name here except ``to_html`` is private to the package (phase 3 rule "Packages").
"""

import re
import unicodedata
from typing import Iterable, List, Union

from textkit.markdown.blocks import (
    Block,
    CodeBlock,
    Heading,
    ListBlock,
    Paragraph,
    Quote,
    Rule,
    parse_blocks,
)
from textkit.markdown.inlines import Code, Emphasis, Inline, Link, Strong, Text, parse_inlines

ALLOWED_SCHEMES = frozenset({"http", "https", "mailto"})
# A scheme name as RFC 3986 and browsers read it: an ASCII letter, then letters, digits,
# "+", "-" or ".". Text before the first ":" that is not one (a path such as
# "/wiki/Help:Contents") means the URL has no scheme: it is relative and kept.
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*")


def escape(text: str) -> str:
    """Escape ``&``, ``<``, ``>`` and ``"`` as HTML entities; nothing else changes.

    ``&`` goes first so that the entities written for the others are not escaped again.
    ``'`` stays (unlike ``html.escape``): the output never uses single-quoted attributes.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _is_ignored_in_scheme(char: str) -> bool:
    # Whitespace and control characters: browsers drop tabs and newlines anywhere in a
    # URL and leading control characters and spaces, so "java\tscript:" runs as
    # "javascript:". Dropping all of them (a superset) can only flag more URLs, never fewer.
    return char.isspace() or unicodedata.category(char) == "Cc"


def safe_url(url: str) -> str:
    """Return ``url`` when it is safe to link to, else ``"#"``.

    The scheme is the text before the first ``:``, with whitespace and control characters
    removed, compared case-insensitively. A URL with no ``:``, or whose text before it is
    not a scheme name (``"/a:b"``, ``"?q=a:b"``), is relative and is kept. A URL whose
    scheme is ``http``, ``https`` or ``mailto`` is kept; any other scheme gives ``"#"``.
    The URL is returned unescaped; the caller escapes it.
    """
    head, colon, _ = url.partition(":")
    if not colon:
        return url
    scheme = "".join(char for char in head if not _is_ignored_in_scheme(char))
    if not _SCHEME.fullmatch(scheme):
        return url
    return url if scheme.lower() in ALLOWED_SCHEMES else "#"


def render_inlines(nodes: Iterable[Inline]) -> str:
    """Render inline nodes as HTML (no line endings are added).

    Iterative, with an explicit stack, so that deeply nested emphasis (thousands of
    ``*a *b *c ...``) cannot exceed Python's recursion limit.
    """
    out: List[str] = []
    # Items to write, last first: a node, or a closing tag already rendered.
    stack: List[Union[Inline, str]] = list(reversed(list(nodes)))
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, Text):
            out.append(escape(node.text))
        elif isinstance(node, Code):
            out.append(f"<code>{escape(node.text)}</code>")
        else:
            if isinstance(node, Emphasis):
                out.append("<em>")
                stack.append("</em>")
            elif isinstance(node, Strong):
                out.append("<strong>")
                stack.append("</strong>")
            elif isinstance(node, Link):
                out.append(f'<a href="{escape(safe_url(node.url))}">')
                stack.append("</a>")
            else:  # pragma: no cover - a new node type must be rendered explicitly
                raise TypeError(f"unknown inline node {node!r}")
            stack.extend(reversed(node.children))
    return "".join(out)


def _inline(text: str) -> str:
    return render_inlines(parse_inlines(text))


def render_blocks(blocks: Iterable[Block]) -> str:
    """Render blocks as HTML, every line ending in ``"\\n"``; no blocks give ``""``."""
    out: List[str] = []
    for block in blocks:
        if isinstance(block, Heading):
            out.append(f"<h{block.level}>{_inline(block.text)}</h{block.level}>\n")
        elif isinstance(block, Paragraph):
            out.append(f"<p>{_inline(block.text)}</p>\n")
        elif isinstance(block, ListBlock):
            tag = "ol" if block.ordered else "ul"
            out.append(f"<{tag}>\n")
            out.extend(f"<li>{_inline(item)}</li>\n" for item in block.items)
            out.append(f"</{tag}>\n")
        elif isinstance(block, CodeBlock):
            if block.language is None:
                out.append("<pre><code>")
            else:
                out.append(f'<pre><code class="language-{escape(block.language)}">')
            out.extend(f"{escape(line)}\n" for line in block.lines)
            out.append("</code></pre>\n")
        elif isinstance(block, Quote):
            out.append("<blockquote>\n")
            out.extend(f"<p>{_inline(paragraph)}</p>\n" for paragraph in block.paragraphs)
            out.append("</blockquote>\n")
        elif isinstance(block, Rule):
            out.append("<hr>\n")
        else:  # pragma: no cover - a new block type must be rendered explicitly
            raise TypeError(f"unknown block {block!r}")
    return "".join(out)


def to_html(text: str) -> str:
    """Convert ``text``, written in textkit's Markdown subset, to HTML.

    Blocks: ATX headings (``#`` to ``######`` and a space), paragraphs, one-level lists
    (``-``/``*`` or ``1.``), fenced code blocks (three backticks and an optional language),
    block quotes of paragraphs and ``---`` rules. Inlines: ``**strong**``, ``*em*``,
    `` `code` ``, ``[text](url)`` and backslash escapes of ``\\ * ` [ ]``. Lines end at
    ``"\\n"``, ``"\\r\\n"`` or ``"\\r"``; every output line ends in ``"\\n"``; ``""`` gives
    ``""``. ``&``, ``<``, ``>`` and ``"`` are always escaped, so raw HTML is printed as
    text, and a link whose scheme is not ``http``, ``https`` or ``mailto`` points to ``#``.
    The full rules and what the subset leaves out are in ADR 0009 and docs/markdown.md.

    Every ``str`` is valid input: unmatched markers are printed as they are.

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"to_html() expects str, got {type(text).__name__}")
    return render_blocks(parse_blocks(text))
