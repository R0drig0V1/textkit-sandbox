"""Tests for ``textkit/markdown/inlines.py``: inline nodes from raw text (plan task T3.5).

The parser is tested on its node output (``Text``, ``Code``, ``Emphasis``, ``Strong``,
``Link``), before any HTML escaping, so these tests pin the inline rules of the Markdown ADR
(docs/decisions/*-markdown-subset-raw-html-and-link-schemes.md) on their own.
"""

import unittest

from textkit.markdown.inlines import Code, Emphasis, Link, Strong, Text, parse_inlines


class ParseInlinesTest(unittest.TestCase):
    def test_plain_text_is_one_node(self):
        self.assertEqual(parse_inlines(""), [])
        self.assertEqual(parse_inlines("a <b> & c"), [Text("a <b> & c")])

    def test_strong_and_emphasis(self):
        self.assertEqual(
            parse_inlines("**a** and *b*"),
            [Strong((Text("a"),)), Text(" and "), Emphasis((Text("b"),))],
        )

    def test_nesting(self):
        self.assertEqual(
            parse_inlines("*a **b** c*"),
            [Emphasis((Text("a "), Strong((Text("b"),)), Text(" c")))],
        )
        self.assertEqual(
            parse_inlines("***a***"), [Emphasis((Strong((Text("a"),)),))]
        )
        self.assertEqual(
            parse_inlines("*a *b* c*"),
            [Emphasis((Text("a "), Emphasis((Text("b"),)), Text(" c")))],
        )

    def test_unmatched_stars_are_text(self):
        self.assertEqual(parse_inlines("**a"), [Text("**a")])
        self.assertEqual(parse_inlines("a * b"), [Text("a * b")])
        self.assertEqual(parse_inlines("a*"), [Text("a*")])
        self.assertEqual(parse_inlines("**a*"), [Text("*"), Emphasis((Text("a"),))])
        self.assertEqual(parse_inlines("*a**"), [Emphasis((Text("a"),)), Text("*")])

    def test_flanking_rule(self):
        # A run opens when no whitespace follows it and closes when none precedes it.
        self.assertEqual(parse_inlines("* a*"), [Text("* a*")])
        self.assertEqual(parse_inlines("*a *"), [Text("*a *")])
        self.assertEqual(parse_inlines("2*3*4"), [Text("2"), Emphasis((Text("3"),)), Text("4")])
        self.assertEqual(
            parse_inlines("**a** b **c**"),
            [Strong((Text("a"),)), Text(" b "), Strong((Text("c"),))],
        )

    def test_code_spans(self):
        self.assertEqual(parse_inlines("`a *b*`"), [Code("a *b*")])
        self.assertEqual(parse_inlines("``a`b``"), [Code("a`b")])
        self.assertEqual(parse_inlines("` a `"), [Code(" a ")])
        self.assertEqual(parse_inlines("`a``"), [Text("`a``")])
        self.assertEqual(parse_inlines("``"), [Text("``")])

    def test_code_span_binds_before_emphasis(self):
        self.assertEqual(parse_inlines("*a`*`*"), [Emphasis((Text("a"), Code("*")))])
        self.assertEqual(parse_inlines("`*`a*"), [Code("*"), Text("a*")])

    def test_backslash_escapes(self):
        self.assertEqual(parse_inlines("\\*a\\*"), [Text("*a*")])
        self.assertEqual(parse_inlines("\\`a\\`"), [Text("`a`")])
        self.assertEqual(parse_inlines("\\[a\\](b)"), [Text("[a](b)")])
        self.assertEqual(parse_inlines("\\\\*a*"), [Text("\\"), Emphasis((Text("a"),))])

    def test_backslash_before_anything_else_is_kept(self):
        self.assertEqual(parse_inlines("\\a \\( \\#"), [Text("\\a \\( \\#")])
        self.assertEqual(parse_inlines("end\\"), [Text("end\\")])

    def test_backslash_is_a_character_in_code(self):
        self.assertEqual(parse_inlines("`\\`"), [Code("\\")])
        self.assertEqual(parse_inlines("`a\\*`"), [Code("a\\*")])

    def test_links(self):
        self.assertEqual(
            parse_inlines("see [the *site*]( https://x.test/a b )!"),
            [
                Text("see "),
                Link((Text("the "), Emphasis((Text("site"),))), "https://x.test/a b"),
                Text("!"),
            ],
        )
        self.assertEqual(parse_inlines("[](u)"), [Link((), "u")])
        self.assertEqual(parse_inlines("[a]()"), [Link((Text("a"),), "")])

    def test_link_url_ends_at_the_first_paren(self):
        self.assertEqual(
            parse_inlines("[a](x(1))"), [Link((Text("a"),), "x(1"), Text(")")]
        )

    def test_what_is_not_a_link(self):
        for text in ("[a]", "[a] (b)", "[a](b", "[a", "a]"):
            with self.subTest(text=text):
                self.assertEqual(parse_inlines(text), [Text(text)])

    def test_links_do_not_nest_and_escaped_brackets_stay_in_the_text(self):
        self.assertEqual(
            parse_inlines("[a [b](c)"), [Text("[a "), Link((Text("b"),), "c")]
        )
        self.assertEqual(parse_inlines("[a\\]b](c)"), [Link((Text("a]b"),), "c")])
        self.assertEqual(parse_inlines("[`]`](c)"), [Link((Code("]"),), "c")])

    def test_emphasis_does_not_cross_a_link_edge(self):
        self.assertEqual(
            parse_inlines("*a [b* c](u)"),
            [Text("*a "), Link((Text("b* c"),), "u")],
        )


if __name__ == "__main__":
    unittest.main()
