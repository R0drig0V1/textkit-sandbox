"""Tests for textkit/markdown/inlines.py: emphasis, code spans, links, escapes (plan task T3.5).

``render_inlines`` is tested directly, on the text of one block; the block structure around
it is tested in tests/test_markdown_blocks.py and the whole conversion in
tests/test_markdown.py.
"""

import time
import unittest

from textkit.markdown.inlines import ESCAPABLE, render_inlines


class RenderInlinesTest(unittest.TestCase):
    def test_plain_text_is_escaped_only(self):
        self.assertEqual(render_inlines('a < b & "c"'), "a &lt; b &amp; &quot;c&quot;")
        self.assertEqual(render_inlines(""), "")

    def test_strong_and_em(self):
        self.assertEqual(render_inlines("**a** and *b*"), "<strong>a</strong> and <em>b</em>")

    def test_nesting(self):
        self.assertEqual(render_inlines("**a *b* c**"), "<strong>a <em>b</em> c</strong>")
        self.assertEqual(render_inlines("*a **b** c*"), "<em>a <strong>b</strong> c</em>")
        self.assertEqual(render_inlines("**[x](/y)**"), '<strong><a href="/y">x</a></strong>')

    def test_star_runs_are_used_from_their_inner_side(self):
        self.assertEqual(render_inlines("**a *b***"), "<strong>a <em>b</em></strong>")
        # Both runs have two stars or more: strong first, inside (as CommonMark does).
        self.assertEqual(render_inlines("***x***"), "<em><strong>x</strong></em>")
        self.assertEqual(render_inlines("*a **b***"), "<em>a <strong>b</strong></em>")
        self.assertEqual(render_inlines("**a**b*"), "<strong>a</strong>b*")

    def test_markers_next_to_whitespace_do_not_open_or_close(self):
        self.assertEqual(render_inlines("2 * 3 * 4"), "2 * 3 * 4")
        self.assertEqual(render_inlines("** a**"), "** a**")
        # The first "*" before a space is skipped; the next one closes.
        self.assertEqual(render_inlines("*a * b*"), "<em>a * b</em>")

    def test_unmatched_markers_print_as_is(self):
        cases = {
            "**a": "**a",
            "*a": "*a",
            "a*": "a*",
            "**": "**",
            "****": "****",
            "**a*": "*<em>a</em>",
            "`a": "`a",
            "``": "``",
            "[a]": "[a]",
            "[a](b": "[a](b",
            "[a] (b)": "[a] (b)",
            "]": "]",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(render_inlines(text), expected)

    def test_code_span_content_is_escaped_and_literal(self):
        self.assertEqual(render_inlines("`<b>&`"), "<code>&lt;b&gt;&amp;</code>")
        # A backslash is a character inside code, and markers are not parsed there.
        self.assertEqual(render_inlines("`a\\*b *c*`"), "<code>a\\*b *c*</code>")

    def test_backslash_escapes(self):
        for char in ESCAPABLE:
            with self.subTest(char=char):
                self.assertEqual(render_inlines("\\" + char), char)
        self.assertEqual(render_inlines("\\*not em\\*"), "*not em*")
        self.assertEqual(render_inlines("\\[not](link)"), "[not](link)")

    def test_backslash_before_other_characters_is_kept(self):
        self.assertEqual(render_inlines("\\_ \\# \\a"), "\\_ \\# \\a")
        self.assertEqual(render_inlines("end\\"), "end\\")
        self.assertEqual(render_inlines("\\<"), "\\&lt;")

    def test_links(self):
        self.assertEqual(
            render_inlines("[a *b*](https://x.org/?q=1&r=2)"),
            '<a href="https://x.org/?q=1&amp;r=2">a <em>b</em></a>',
        )
        self.assertEqual(render_inlines("[](/x)"), '<a href="/x"></a>')
        self.assertEqual(render_inlines("[a\\]b](/x)"), '<a href="/x">a]b</a>')

    def test_link_schemes_go_through_the_allowlist(self):
        self.assertEqual(render_inlines("[x](javascript:alert)"), '<a href="#">x</a>')
        self.assertEqual(render_inlines("[x](JaVaScRiPt:alert)"), '<a href="#">x</a>')
        self.assertEqual(render_inlines("[x](mailto:a@b.c)"), '<a href="mailto:a@b.c">x</a>')

    def test_link_url_is_escaped(self):
        self.assertEqual(
            render_inlines('[x]("><script>)'), '<a href="&quot;&gt;&lt;script&gt;">x</a>'
        )

    def test_markers_inside_code_and_links_do_not_close_emphasis(self):
        self.assertEqual(render_inlines("*a `*` b*"), "<em>a <code>*</code> b</em>")
        self.assertEqual(
            render_inlines("*see [x*y](/u)*"), '<em>see <a href="/u">x*y</a></em>'
        )
        self.assertEqual(render_inlines("*a \\* b*"), "<em>a * b</em>")


    def test_long_star_runs_keep_every_star(self):
        # A run that can neither open nor close is text, however long (it once recursed).
        for n in (1, 2, 5000, 10000):
            with self.subTest(n=n):
                self.assertEqual(render_inlines("*" * n), "*" * n)
        self.assertEqual(render_inlines("x" + "*" * 10000), "x" + "*" * 10000)

    def test_deep_nesting_does_not_recurse(self):
        n = 5000
        self.assertEqual(
            render_inlines("**" * n + "a" + "**" * n), "<strong>" * n + "a" + "</strong>" * n
        )
        self.assertEqual(render_inlines("*a " * n + "b" + "*" * n), "<em>a " * n + "b" + "</em>" * n)
        self.assertEqual(
            render_inlines("[" * n + "x" + "](/u)" * n), "[" * (n - 1) + '<a href="/u">x</a>' + "](/u)" * (n - 1)
        )

    def test_unmatched_openers_take_linear_time(self):
        # Each of these took seconds to minutes with a scan per opener; one pass takes
        # milliseconds. The bound is generous so a loaded machine does not fail it.
        for text in ("[" * 20000, "*a " * 20000, "a*" * 20000, "](" * 20000, "[a](" * 20000,
                     "`a" * 20000, "\\[" * 20000):
            with self.subTest(text=text[:8]):
                start = time.perf_counter()
                render_inlines(text)
                self.assertLess(time.perf_counter() - start, 2.0)

    def test_link_closes_the_nearest_open_bracket(self):
        self.assertEqual(render_inlines("[a [b](/c)"), '[a <a href="/c">b</a>')
        # No link inside a link: once [b](/c) is made, the outer "[" is text.
        self.assertEqual(render_inlines("[a [b](/c)](/d)"), '[a <a href="/c">b</a>](/d)')
        self.assertEqual(render_inlines("[*a](/u)*"), '<a href="/u">*a</a>*')


if __name__ == "__main__":
    unittest.main()
