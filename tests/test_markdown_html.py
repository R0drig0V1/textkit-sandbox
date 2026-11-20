"""Tests for ``textkit/markdown/html.py``: escaping, link schemes and the output layout (T3.5).

``escape``, ``safe_url``, ``render_inlines`` and ``render_blocks`` are tested on hand-built
nodes, so the HTML rules of the Markdown ADR
(docs/decisions/*-markdown-subset-raw-html-and-link-schemes.md) are pinned independently of
the parsers.
"""

import unittest

from textkit.markdown.blocks import CodeBlock, Heading, ListBlock, Paragraph, Quote, Rule
from textkit.markdown.html import escape, render_blocks, render_inlines, safe_url
from textkit.markdown.inlines import Code, Emphasis, Link, Strong, Text


class EscapeTest(unittest.TestCase):
    def test_escapes_the_four_characters(self):
        self.assertEqual(escape('<a href="x">&</a>'), "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;")

    def test_ampersand_first_so_entities_are_not_escaped_twice(self):
        self.assertEqual(escape("&lt;"), "&amp;lt;")

    def test_everything_else_is_unchanged(self):
        text = "it's ñ \t \\ ` *"
        self.assertEqual(escape(text), text)


class SafeUrlTest(unittest.TestCase):
    def test_allowed_schemes_are_kept(self):
        for url in ("http://a.test", "https://a.test/x?y=1", "mailto:a@b.test",
                    "HTTPS://A.TEST", "MailTo:a@b.test"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), url)

    def test_other_schemes_become_hash(self):
        for url in ("javascript:alert(1)", "JaVaScRiPt:alert(1)", "data:text/html,x",
                    "vbscript:x", "ftp://a.test", "file:///etc/passwd", "x:"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), "#")

    def test_whitespace_and_control_characters_are_ignored_in_the_scheme(self):
        for url in ("java\tscript:x", " javascript:x", "java\nscript:x", "\x00javascript:x",
                    "jav\x1fascript:x", "java\u00a0script:x", "\x7fjavascript:x"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), "#")
        self.assertEqual(safe_url(" https://a.test"), " https://a.test")

    def test_urls_without_a_scheme_are_kept(self):
        for url in ("", "page.html", "/a/b", "#top", "?q=1", "/wiki/Help:Contents",
                    "?q=a:b", "./x:y", ":x", "1http:x", "naïve:x"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), url)


class RenderInlinesTest(unittest.TestCase):
    def test_every_node(self):
        nodes = [
            Text("a<"),
            Code("&"),
            Emphasis((Text("e"),)),
            Strong((Text("s"),)),
            Link((Text("l"),), "/x"),
        ]
        self.assertEqual(
            render_inlines(nodes),
            'a&lt;<code>&amp;</code><em>e</em><strong>s</strong><a href="/x">l</a>',
        )

    def test_link_url_is_checked_then_escaped(self):
        self.assertEqual(
            render_inlines([Link((Text("x"),), 'https://a.test/?a=1&b="2"')]),
            '<a href="https://a.test/?a=1&amp;b=&quot;2&quot;">x</a>',
        )
        self.assertEqual(
            render_inlines([Link((Text("x"),), "javascript:alert(1)")]), '<a href="#">x</a>'
        )

    def test_deep_nesting_does_not_recurse(self):
        node = Text("x")
        for _ in range(5000):
            node = Emphasis((node,))
        self.assertEqual(render_inlines([node]), "<em>" * 5000 + "x" + "</em>" * 5000)


class RenderBlocksTest(unittest.TestCase):
    def test_no_blocks(self):
        self.assertEqual(render_blocks([]), "")

    def test_heading_paragraph_and_rule(self):
        self.assertEqual(
            render_blocks([Heading(3, "*t*"), Paragraph("a b"), Rule()]),
            "<h3><em>t</em></h3>\n<p>a b</p>\n<hr>\n",
        )

    def test_lists(self):
        self.assertEqual(
            render_blocks([ListBlock(False, ("a", "b")), ListBlock(True, ("c",))]),
            "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n<ol>\n<li>c</li>\n</ol>\n",
        )

    def test_quote(self):
        self.assertEqual(
            render_blocks([Quote(("a", "b"))]),
            "<blockquote>\n<p>a</p>\n<p>b</p>\n</blockquote>\n",
        )

    def test_code_blocks(self):
        self.assertEqual(
            render_blocks([CodeBlock("py", ("if a<b:", "  *x*", ""))]),
            '<pre><code class="language-py">if a&lt;b:\n  *x*\n\n</code></pre>\n',
        )
        self.assertEqual(render_blocks([CodeBlock(None, ())]), "<pre><code></code></pre>\n")
        self.assertEqual(
            render_blocks([CodeBlock('"><x', ())]),
            '<pre><code class="language-&quot;&gt;&lt;x"></code></pre>\n',
        )


if __name__ == "__main__":
    unittest.main()
