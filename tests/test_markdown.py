"""Tests for ``textkit.markdown.to_html`` (plan task T3.5) and its guide, docs/markdown.md.

- ``MARKDOWN_CASES`` is the case table of the Markdown ADR
  (docs/decisions/*-markdown-subset-escaping-and-link-schemes.md), row by row and in the
  same order; ``ToHtmlTest`` converts every row and checks that the ADR's table, parsed
  with ``ast.literal_eval``, equals this list, so the two cannot drift apart.
- ``load_tests`` runs the ``>>>`` examples of docs/markdown.md as doctests.
- ``MarkdownCommandTest`` runs ``python3 -m textkit markdown <file>`` (textkit/cli/markdown.py)
  in a subprocess, through ``_run`` and ``_run_bytes`` of tests/test_cli.py, with its input
  files in a ``tempfile`` directory.

The modules of the package are tested one by one in tests/test_markdown_blocks.py,
tests/test_markdown_inlines.py and tests/test_markdown_html.py.
"""

import ast
import doctest
import pathlib
import re
import tempfile
import unittest

import textkit.markdown
from textkit.markdown import to_html
from tests.test_cli import _run, _run_bytes

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "markdown.md"

# (input, output) for every row of the ADR's "## Cases" table, in order.
MARKDOWN_CASES = [
    ("", ""),
    ("# Title", "<h1>Title</h1>\n"),
    ("###### Six", "<h6>Six</h6>\n"),
    ("####### Seven", "<p>####### Seven</p>\n"),
    ("#NoSpace", "<p>#NoSpace</p>\n"),
    ("one\ntwo\n\nthree", "<p>one two</p>\n<p>three</p>\n"),
    ("- a\n- b", "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n"),
    ("* a\n  more\n- b", "<ul>\n<li>a more</li>\n<li>b</li>\n</ul>\n"),
    ("1. a\n7. b", "<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n"),
    ("- a\nnext", "<ul>\n<li>a</li>\n</ul>\n<p>next</p>\n"),
    ("```\nx\n```", "<pre><code>x\n</code></pre>\n"),
    ("```python\nprint(1)\n\n```", "<pre><code class=\"language-python\">print(1)\n\n</code></pre>\n"),
    ("```\nunclosed", "<pre><code>unclosed\n</code></pre>\n"),
    ("> a\n> b\n>\n> c", "<blockquote>\n<p>a b</p>\n<p>c</p>\n</blockquote>\n"),
    ("> # not a heading\n> - not an item", "<blockquote>\n<p># not a heading - not an item</p>\n</blockquote>\n"),
    ("---", "<hr>\n"),
    ("text\n# Heading", "<p>text</p>\n<h1>Heading</h1>\n"),
    ("text\n- item", "<p>text</p>\n<ul>\n<li>item</li>\n</ul>\n"),
    ("text\n```\ncode\n```", "<p>text</p>\n<pre><code>code\n</code></pre>\n"),
    ("text\n> quote", "<p>text</p>\n<blockquote>\n<p>quote</p>\n</blockquote>\n"),
    ("text\n---", "<p>text</p>\n<hr>\n"),
    ("**strong**", "<p><strong>strong</strong></p>\n"),
    ("*em*", "<p><em>em</em></p>\n"),
    ("**a *b* c**", "<p><strong>a <em>b</em> c</strong></p>\n"),
    ("***x***", "<p><em><strong>x</strong></em></p>\n"),
    ("**** ** a **", "<p>**** ** a **</p>\n"),
    ("`code`", "<p><code>code</code></p>\n"),
    ("[text](https://example.com)", "<p><a href=\"https://example.com\">text</a></p>\n"),
    ("[mail](mailto:a@example.com)", "<p><a href=\"mailto:a@example.com\">mail</a></p>\n"),
    ("[rel](docs/a.md)", "<p><a href=\"docs/a.md\">rel</a></p>\n"),
    ("[js](javascript:alert)", "<p><a href=\"#\">js</a></p>\n"),
    ("[js](JaVaScRiPt:alert)", "<p><a href=\"#\">js</a></p>\n"),
    ("[js](java\tscript:alert)", "<p><a href=\"#\">js</a></p>\n"),
    ("[data](data:text/html,x)", "<p><a href=\"#\">data</a></p>\n"),
    ("[up](HTTPS://example.com)", "<p><a href=\"HTTPS://example.com\">up</a></p>\n"),
    ("[js](\x01javascript:alert)", "<p><a href=\"#\">js</a></p>\n"),
    ("[t](/a?t=10:30)", "<p><a href=\"#\">t</a></p>\n"),
    ("\\*a\\* \\` \\[b\\] \\\\", "<p>*a* ` [b] \\</p>\n"),
    ("\\_ \\#", "<p>\\_ \\#</p>\n"),
    ("`a\\*b`", "<p><code>a\\*b</code></p>\n"),
    ("**a", "<p>**a</p>\n"),
    ("*a", "<p>*a</p>\n"),
    ("2 * 3 * 4", "<p>2 * 3 * 4</p>\n"),
    ("`a", "<p>`a</p>\n"),
    ("[a]", "<p>[a]</p>\n"),
    ("<b>&\"x\"'</b>", "<p>&lt;b&gt;&amp;&quot;x&quot;'&lt;/b&gt;</p>\n"),
    ("`<a href=\"x\">`", "<p><code>&lt;a href=&quot;x&quot;&gt;</code></p>\n"),
    ("```\n<script>&\n```", "<pre><code>&lt;script&gt;&amp;\n</code></pre>\n"),
    ("```a\"b\nx\n```", "<pre><code class=\"language-a&quot;b\">x\n</code></pre>\n"),
    ("[a](\"><script>)", "<p><a href=\"&quot;&gt;&lt;script&gt;\">a</a></p>\n"),
    ("# Title\r\n", "<h1>Title</h1>\n"),
    ("```py\r\nx = 1\r\n```\r\n", "<pre><code class=\"language-py\">x = 1\n</code></pre>\n"),
    ("a\rb", "<p>a b</p>\n"),
]

# A row of the ADR table: two cells, each a Python literal in one code span. The ADR writes
# a backtick as \x60, so a cell never contains one.
_ROW = re.compile(r"^\| `([^`]*)` \| `([^`]*)` \|$", re.M)


def _adr_cases() -> list:
    """Parse the Markdown ADR's case table into (input, output) pairs, found by slug."""
    (adr,) = (ROOT / "docs" / "decisions").glob("*-markdown-subset-escaping-and-link-schemes.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    return [(ast.literal_eval(a), ast.literal_eval(b)) for a, b in _ROW.findall(table)]


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: object
) -> unittest.TestSuite:
    """Add the examples of docs/markdown.md to the tests unittest found in this module."""
    tests.addTest(doctest.DocFileSuite(str(GUIDE), module_relative=False, encoding="utf-8"))
    return tests


class ToHtmlTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in MARKDOWN_CASES:
            with self.subTest(text=text):
                self.assertEqual(to_html(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(MARKDOWN_CASES, _adr_cases())

    def test_adr_table_covers_what_the_plan_requires(self):
        inputs = [text for text, _ in MARKDOWN_CASES]
        outputs = "".join(html for _, html in MARKDOWN_CASES)
        for tag in ("<h1>", "<p>", "<ul>", "<ol>", "<pre><code", "<blockquote>", "<hr>",
                    "<strong>", "<em>", "<code>", "<a href=", "&lt;", "&gt;", "&amp;", "&quot;"):
            with self.subTest(tag=tag):
                self.assertIn(tag, outputs)
        self.assertIn("[js](javascript:alert)", inputs)
        self.assertIn("[js](JaVaScRiPt:alert)", inputs)
        self.assertIn("# Title\r\n", inputs)
        self.assertTrue(any(t.startswith("```py") and "\r\n" in t for t in inputs))

    def test_public_api(self):
        self.assertEqual(textkit.markdown.__all__, ["to_html"])
        self.assertIs(textkit.markdown.to_html, to_html)

    def test_empty_and_blank_give_empty(self):
        for text in ("", "\n", "\r\n", "  \n\t\r"):
            with self.subTest(text=text):
                self.assertEqual(to_html(text), "")

    def test_every_line_ends_in_newline(self):
        for text, _ in MARKDOWN_CASES:
            html = to_html(text)
            with self.subTest(text=text):
                self.assertTrue(html == "" or html.endswith("\n"))
                self.assertNotIn("\r", html)
                # No whitespace is added: outside code blocks there is no empty line.
                if "<pre>" not in html:
                    self.assertNotIn("\n\n", html)

    def test_line_endings_give_the_same_html(self):
        text = "# T\n\npara\none\n\n- a\n  b\n\n```py\nx\n\ny\n```\n> q\n"
        expected = to_html(text)
        for ending in ("\r\n", "\r"):
            with self.subTest(ending=ending):
                self.assertEqual(to_html(text.replace("\n", ending)), expected)

    def test_a_document(self):
        text = (
            "# Notes\n"
            "\n"
            "Some *text* with `code`\n"
            "and a [link](https://example.com).\n"
            "- one\n"
            "- two\n"
            "\n"
            "1. first\n"
            "\n"
            "> quoted\n"
            "\n"
            "---\n"
            "```sh\n"
            "echo '<hi>'\n"
            "```\n"
        )
        self.assertEqual(
            to_html(text),
            "<h1>Notes</h1>\n"
            "<p>Some <em>text</em> with <code>code</code>"
            ' and a <a href="https://example.com">link</a>.</p>\n'
            "<ul>\n<li>one</li>\n<li>two</li>\n</ul>\n"
            "<ol>\n<li>first</li>\n</ol>\n"
            "<blockquote>\n<p>quoted</p>\n</blockquote>\n"
            "<hr>\n"
            '<pre><code class="language-sh">echo \'&lt;hi&gt;\'\n</code></pre>\n',
        )

    def test_no_raw_html_reaches_the_output(self):
        text = '<script>alert("x")</script>\n# <img src=x onerror=y>\n- <b>\n> <i>\n`<u>`'
        html = to_html(text)
        for tag in ("<script", "<img", "<b>", "<i>", "<u>"):
            with self.subTest(tag=tag):
                self.assertNotIn(tag, html)

    def test_long_and_deep_input_never_raises(self):
        n = 10000
        self.assertEqual(to_html("*" * n), "<p>" + "*" * n + "</p>\n")
        self.assertEqual(
            to_html("- " + "**" * n + "a" + "**" * n),
            "<ul>\n<li>" + "<strong>" * n + "a" + "</strong>" * n + "</li>\n</ul>\n",
        )

    def test_rejects_non_str(self):
        for bad in (None, b"# x", 3, ["# x"]):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    to_html(bad)  # type: ignore[arg-type]



class MarkdownCommandTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = pathlib.Path(tmp.name)

    def _file(self, name: str, data: bytes) -> str:
        path = self.dir / name
        path.write_bytes(data)
        return str(path)

    def test_writes_the_html_and_exits_0(self):
        text = "# Title\n\nSome *text* & <b>.\n"
        result = _run("markdown", self._file("a.md", text.encode("utf-8")))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, to_html(text))
        self.assertEqual(result.stderr, "")

    def test_crlf_file(self):
        # Read with newline="": the function sees the "\r\n"; the HTML has "\n" only.
        data = "# Title\r\n\r\n```py\r\nx = 1\r\n```\r\n".encode("utf-8")
        result = _run_bytes("markdown", self._file("crlf.md", data))
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = '<h1>Title</h1>\n<pre><code class="language-py">x = 1\n</code></pre>\n'
        self.assertEqual(result.stdout, expected.encode("utf-8"))

    def test_non_ascii_round_trips(self):
        text = "*Ñandú* — café\n"
        result = _run_bytes("markdown", self._file("u.md", text.encode("utf-8")))
        self.assertEqual(result.stdout, "<p><em>Ñandú</em> — café</p>\n".encode("utf-8"))

    def test_empty_file_writes_nothing(self):
        result = _run_bytes("markdown", self._file("empty.md", b"\n\n"))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_long_star_run_exits_0(self):
        # Once a RecursionError with a traceback and exit 1.
        result = _run("markdown", self._file("stars.md", b"*" * 10000 + b"\n"))
        self.assertEqual(result.returncode, 0, result.stderr[-500:])
        self.assertEqual(result.stdout, "<p>" + "*" * 10000 + "</p>\n")
        self.assertEqual(result.stderr, "")

    def test_missing_file_exits_2(self):
        path = str(self.dir / "missing.md")
        result = _run("markdown", path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(
            result.stderr.startswith(f"python3 -m textkit markdown: error: {path}: "),
            result.stderr,
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_directory_exits_2(self):
        result = _run("markdown", str(self.dir))
        self.assertEqual(result.returncode, 2)
        self.assertIn(f"python3 -m textkit markdown: error: {self.dir}: ", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_exits_2(self):
        path = self._file("latin1.md", "café".encode("latin-1"))
        result = _run("markdown", path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr, f"python3 -m textkit markdown: error: {path}: not valid UTF-8 (byte 3)\n"
        )

    def test_listed_under_tools_in_help(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        tools = result.stdout.split("tools:", 1)[1]
        self.assertRegex(tools, r"(?m)^  markdown +Convert a Markdown file to HTML")


if __name__ == "__main__":
    unittest.main()
