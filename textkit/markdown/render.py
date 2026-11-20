"""``to_html``: the public entry point of ``textkit.markdown``, blocks to HTML text.

``blocks.parse_blocks`` finds the blocks, ``inlines.render_inlines`` renders the text inside
them, and this module writes each block in the exact shape the plan (task T3.5) and the
Markdown ADR fix: one element per line, every line ending in ``"\\n"``, no other whitespace.
"""

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
from textkit.markdown.html import escape
from textkit.markdown.inlines import render_inlines


def _paragraph(text: str) -> str:
    return f"<p>{render_inlines(text)}</p>\n"


def _block_html(block: Block) -> str:
    """The HTML of one block, every line of it ending in ``"\\n"``."""
    if isinstance(block, Heading):
        return f"<h{block.level}>{render_inlines(block.text)}</h{block.level}>\n"
    if isinstance(block, Paragraph):
        return _paragraph(block.text)
    if isinstance(block, Rule):
        return "<hr>\n"
    if isinstance(block, ListBlock):
        tag = "ol" if block.ordered else "ul"
        items = "".join(f"<li>{render_inlines(item)}</li>\n" for item in block.items)
        return f"<{tag}>\n{items}</{tag}>\n"
    if isinstance(block, Quote):
        paragraphs = "".join(_paragraph(text) for text in block.paragraphs)
        return f"<blockquote>\n{paragraphs}</blockquote>\n"
    if isinstance(block, CodeBlock):
        attribute = "" if block.language is None else f' class="language-{escape(block.language)}"'
        # The content follows the opening tag directly: a newline there would be a blank
        # first line of code in the rendered page.
        content = "".join(f"{escape(line)}\n" for line in block.lines)
        return f"<pre><code{attribute}>{content}</code></pre>\n"
    # Unreachable: every Block type is handled above.
    raise TypeError(f"not a Markdown block: {block!r}")


def to_html(text: str) -> str:
    """Convert the Markdown subset of ``textkit.markdown`` in ``text`` to HTML.

    Blocks: ATX headings, paragraphs, one-level unordered and ordered lists, fenced code
    blocks, block quotes of paragraphs and ``---`` rules. Inlines: ``**strong**``,
    ``*em*``, ```code```, ``[text](url)`` and backslash escapes of ``\\ * ` [ ]``. The
    exact rules, and what the subset leaves out, are in docs/markdown.md and the Markdown
    ADR (docs/decisions/*-markdown-subset-escaping-and-link-schemes.md).

    Raw HTML is never passed through: ``&``, ``<``, ``>`` and ``"`` are escaped everywhere,
    code included. A link whose scheme is not ``http``, ``https`` or ``mailto`` points to
    ``#``; a relative link is kept.

    Lines may end in ``"\\n"``, ``"\\r\\n"`` or ``"\\r"``; every line of the result ends in
    ``"\\n"``, and ``""`` (or blank text) gives ``""``.

    Raises:
        TypeError: ``text`` is not a ``str``. Any ``str`` is accepted: text that is not
            valid Markdown of the subset is printed as is, escaped.
    """
    if not isinstance(text, str):
        raise TypeError(f"to_html() expects a str, not {type(text).__name__}")
    return "".join(_block_html(block) for block in parse_blocks(text))
