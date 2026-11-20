"""Markdown to HTML for a small, safe subset of Markdown (plan task T3.5).

The package has three stages, one module each:

- ``blocks.py`` splits the text into lines and groups them into blocks (headings,
  paragraphs, lists, fenced code, block quotes, horizontal rules);
- ``inlines.py`` parses the text of a block into inline nodes (strong, emphasis, code
  spans, links, backslash escapes);
- ``html.py`` renders blocks and inline nodes as HTML, escaping every ``&``, ``<``, ``>``
  and ``"`` and replacing links with an unsafe scheme by ``#``; it also defines ``to_html``,
  the only public function.

What the subset leaves out, why raw HTML is escaped and why some link schemes are dropped
are decided in docs/decisions/0007-markdown-subset-raw-html-and-link-schemes.md; the syntax
is described with examples in docs/markdown.md.
"""

from textkit.markdown.html import to_html

# Functions only (phase 3 rule "Packages"): scripts/check.sh asks a README row for each name.
__all__ = ["to_html"]
