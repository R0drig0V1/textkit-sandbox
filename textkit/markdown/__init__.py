"""Markdown to HTML for a small, safe subset of Markdown (plan task T3.5).

The package's one public function is ``to_html`` (``__all__``). Its modules, each private:

- ``blocks``: lines and blocks (headings, paragraphs, lists, code, quotes, rules);
- ``inlines``: emphasis, code spans, links and backslash escapes inside a block;
- ``html``: escaping and the link-scheme allowlist;
- ``render``: ``to_html``, which writes the blocks as HTML.

Guide: docs/markdown.md. Decisions (the subset, escaping, link schemes, with a table of
cases): docs/decisions/*-markdown-subset-escaping-and-link-schemes.md.
"""

from textkit.markdown.render import to_html

__all__ = ["to_html"]
