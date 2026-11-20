"""Tests for ``textkit.markdown.to_html``, the public function of the Markdown tool (T3.5).

The case table of the Markdown ADR (docs/decisions/*-markdown-subset-raw-html-and-link-schemes.md)
is the specification: ``CASES`` below must equal it row for row (parsed with
``ast.literal_eval``) and ``to_html`` must give every output. The modules of the package are
tested directly in ``tests/test_markdown_blocks.py``, ``tests/test_markdown_inlines.py`` and
``tests/test_markdown_html.py``; the subcommand in ``tests/test_markdown_cli.py``.
"""

import ast
import pathlib
import unittest

import textkit.markdown
from textkit.markdown import to_html

ROOT = pathlib.Path(__file__).resolve().parents[1]

# (input, output), in the order of the ADR table.
CASES = [
    ('', ''),
    ('# Title', '<h1>Title</h1>\n'),
    ('###### Six', '<h6>Six</h6>\n'),
    ('####### Seven', '<p>####### Seven</p>\n'),
    ('#NoSpace', '<p>#NoSpace</p>\n'),
    ('one\ntwo', '<p>one two</p>\n'),
    ('one\n\ntwo', '<p>one</p>\n<p>two</p>\n'),
    ('- a\n- b', '<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n'),
    ('* a\n  more\n* b', '<ul>\n<li>a more</li>\n<li>b</li>\n</ul>\n'),
    ('1. a\n7. b', '<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n'),
    ('- a\n\n- b', '<ul>\n<li>a</li>\n</ul>\n<ul>\n<li>b</li>\n</ul>\n'),
    ('- a\n1. b', '<ul>\n<li>a</li>\n</ul>\n<ol>\n<li>b</li>\n</ol>\n'),
    ('```\n<x>\n```', '<pre><code>&lt;x&gt;\n</code></pre>\n'),
    ('```python\nprint(1)\n```', '<pre><code class="language-python">print(1)\n</code></pre>\n'),
    ('```a"b\nx\n```', '<pre><code class="language-a&quot;b">x\n</code></pre>\n'),
    ('```\nno closing fence', '<pre><code>no closing fence\n</code></pre>\n'),
    ('> a\n> b\n>\n> c', '<blockquote>\n<p>a b</p>\n<p>c</p>\n</blockquote>\n'),
    ('> # not a heading', '<blockquote>\n<p># not a heading</p>\n</blockquote>\n'),
    ('> q\n\nafter', '<blockquote>\n<p>q</p>\n</blockquote>\n<p>after</p>\n'),
    ('---', '<hr>\n'),
    ('para\n# Heading', '<p>para</p>\n<h1>Heading</h1>\n'),
    ('para\n- item', '<p>para</p>\n<ul>\n<li>item</li>\n</ul>\n'),
    ('para\n```\ncode\n```', '<p>para</p>\n<pre><code>code\n</code></pre>\n'),
    ('para\n> quote', '<p>para</p>\n<blockquote>\n<p>quote</p>\n</blockquote>\n'),
    ('para\n---', '<p>para</p>\n<hr>\n'),
    ('# Title\r\n', '<h1>Title</h1>\n'),
    ('```py\r\nx = 1\r\n```\r\n', '<pre><code class="language-py">x = 1\n</code></pre>\n'),
    ('a\rb', '<p>a b</p>\n'),
    ('**strong**', '<p><strong>strong</strong></p>\n'),
    ('*em*', '<p><em>em</em></p>\n'),
    ('`code`', '<p><code>code</code></p>\n'),
    ('[text](https://example.com)', '<p><a href="https://example.com">text</a></p>\n'),
    ('*a **b** c*', '<p><em>a <strong>b</strong> c</em></p>\n'),
    ('**unclosed', '<p>**unclosed</p>\n'),
    ('a * b', '<p>a * b</p>\n'),
    ('`unclosed', '<p>`unclosed</p>\n'),
    ('[no url]', '<p>[no url]</p>\n'),
    ('\\* \\` \\[ \\] \\\\', '<p>* ` [ ] \\</p>\n'),
    ('\\a', '<p>\\a</p>\n'),
    ('`\\*`', '<p><code>\\*</code></p>\n'),
    ('<b>&"</b>', '<p>&lt;b&gt;&amp;&quot;&lt;/b&gt;</p>\n'),
    ('`<b>&"</b>`', '<p><code>&lt;b&gt;&amp;&quot;&lt;/b&gt;</code></p>\n'),
    ('[a](https://x.test/?a=1&b="2")', '<p><a href="https://x.test/?a=1&amp;b=&quot;2&quot;">a</a></p>\n'),
    ('[x](javascript:alert(1))', '<p><a href="#">x</a>)</p>\n'),
    ('[x](JaVaScRiPt:alert(1))', '<p><a href="#">x</a>)</p>\n'),
    ('[x](java\tscript:alert(1))', '<p><a href="#">x</a>)</p>\n'),
    ('[x](data:text/html,hi)', '<p><a href="#">x</a></p>\n'),
    ('[x](mailto:a@b.test)', '<p><a href="mailto:a@b.test">x</a></p>\n'),
    ('[x](HTTP://example.com)', '<p><a href="HTTP://example.com">x</a></p>\n'),
    ('[x](/wiki/Help:Contents)', '<p><a href="/wiki/Help:Contents">x</a></p>\n'),
    ('[x](page.html)', '<p><a href="page.html">x</a></p>\n'),
]


def _adr_cases() -> list:
    """Parse the Markdown ADR's case table into (input, output) pairs.

    The ADR is found by its slug, never its number: the integrator may renumber it. Cells
    hold no ``|`` (it is written ``\\x7c``), so a row splits on ``" | "``.
    """
    (adr,) = (ROOT / "docs" / "decisions").glob("*-markdown-subset-raw-html-and-link-schemes.md")
    table = adr.read_text(encoding="utf-8").split("\n## Cases\n", 1)[1]
    rows = []
    for line in table.splitlines():
        if not line.startswith("| `"):
            continue  # prose, the header and the separator row
        cells = line[2:-2].split(" | ")
        rows.append(tuple(ast.literal_eval(cell[1:-1]) for cell in cells))
    return rows


class ToHtmlTest(unittest.TestCase):
    def test_case_list_equals_adr_table(self):
        self.assertEqual(CASES, _adr_cases())

    def test_adr_cases(self):
        for text, expected in CASES:
            with self.subTest(text=text):
                self.assertEqual(to_html(text), expected)

    def test_adr_table_covers_what_the_plan_requires(self):
        inputs = [text for text, _ in CASES]
        outputs = "".join(html for _, html in CASES)
        for tag in ("<h1>", "<p>", "<ul>", "<ol>", "<pre><code", "<blockquote>", "<hr>",
                    "<strong>", "<em>", "<code>", "<a href"):
            with self.subTest(tag=tag):
                self.assertIn(tag, outputs)
        self.assertTrue(any("javascript:" in text for text in inputs))
        self.assertTrue(any("JaVaScRiPt:" in text for text in inputs))
        self.assertTrue(any(t.startswith("#") and "\r\n" in t for t in inputs))
        self.assertTrue(any(t.startswith("```py") and "\r\n" in t for t in inputs))

    def test_empty_text_gives_empty_output(self):
        self.assertEqual(to_html(""), "")
        self.assertEqual(to_html(" \t\n\r\n\r"), "")

    def test_every_output_line_ends_in_newline(self):
        for text, _ in CASES:
            html = to_html(text)
            with self.subTest(text=text):
                if html:
                    self.assertTrue(html.endswith("\n"))
                self.assertNotIn("\r", html)

    def test_line_endings_give_the_same_html(self):
        text = "# T\n\npara\none\n\n- a\n  b\n\n```py\nx\n```\n> q\n"
        expected = to_html(text)
        self.assertEqual(to_html(text.replace("\n", "\r\n")), expected)
        self.assertEqual(to_html(text.replace("\n", "\r")), expected)

    def test_a_document_with_every_block(self):
        text = (
            "# Notes\n"
            "Some *new* **ideas**,\n"
            "see [the site](https://example.com).\n"
            "\n"
            "- first\n"
            "- second `x < y`\n"
            "\n"
            "1. one\n"
            "2. two\n"
            "\n"
            "> quoted\n"
            "---\n"
            "```sh\n"
            "echo <hi>\n"
            "```\n"
        )
        self.assertEqual(
            to_html(text),
            "<h1>Notes</h1>\n"
            "<p>Some <em>new</em> <strong>ideas</strong>, see "
            '<a href="https://example.com">the site</a>.</p>\n'
            "<ul>\n<li>first</li>\n<li>second <code>x &lt; y</code></li>\n</ul>\n"
            "<ol>\n<li>one</li>\n<li>two</li>\n</ol>\n"
            "<blockquote>\n<p>quoted</p>\n</blockquote>\n"
            "<hr>\n"
            '<pre><code class="language-sh">echo &lt;hi&gt;\n</code></pre>\n',
        )

    def test_inlines_in_headings_items_and_quotes(self):
        self.assertEqual(to_html("## *a*"), "<h2><em>a</em></h2>\n")
        self.assertEqual(to_html("- **b**"), "<ul>\n<li><strong>b</strong></li>\n</ul>\n")
        self.assertEqual(
            to_html("> `c`"), "<blockquote>\n<p><code>c</code></p>\n</blockquote>\n"
        )

    def test_no_raw_html_survives(self):
        hostile = '<script>alert("x")</script> <img src=x onerror=alert(1)>'
        for text in (hostile, f"# {hostile}", f"- {hostile}", f"> {hostile}",
                     f"```\n{hostile}\n```", f"`{hostile}`", f"[{hostile}](/a)"):
            with self.subTest(text=text):
                html = to_html(text)
                self.assertNotIn("<script", html)
                self.assertNotIn("<img", html)
                self.assertNotIn('"x"', html)

    def test_hostile_input_is_fast_and_does_not_recurse(self):
        # Unmatched or deeply nested markers: linear-ish time, no RecursionError.
        for text in ("a* " * 20000, "*a " * 5000 + "a* " * 5000, "`x ``y " * 5000,
                     "[a](" * 20000):
            with self.subTest(text=text[:12]):
                self.assertTrue(to_html(text).startswith("<p>"))

    def test_rejects_non_str(self):
        for value in (None, b"# x", 1):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_html(value)  # type: ignore[arg-type]

    def test_package_exports_only_to_html(self):
        self.assertEqual(textkit.markdown.__all__, ["to_html"])
        self.assertIs(textkit.markdown.to_html, to_html)


if __name__ == "__main__":
    unittest.main()
