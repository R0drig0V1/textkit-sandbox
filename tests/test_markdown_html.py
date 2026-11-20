"""Tests for textkit/markdown/html.py: escaping and the link-scheme allowlist (plan task T3.5).

The rules come from the Markdown ADR
(docs/decisions/*-markdown-subset-escaping-and-link-schemes.md): ``&``, ``<``, ``>`` and
``"`` are escaped, and a link keeps its URL only when it is relative or its scheme is
``http``, ``https`` or ``mailto``.
"""

import unittest

from textkit.markdown import html
from textkit.markdown.html import BLOCKED_URL, escape, safe_url


class EscapeTest(unittest.TestCase):
    def test_escapes_the_four_characters(self):
        self.assertEqual(escape('<a href="x">&</a>'), "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;")

    def test_ampersand_is_escaped_once(self):
        # "&" goes first: the entities written for "<" are not escaped again.
        self.assertEqual(escape("<&lt;"), "&lt;&amp;lt;")

    def test_single_quote_is_kept(self):
        # Every attribute textkit writes is double-quoted, so "'" cannot end one.
        self.assertEqual(escape("it's"), "it's")

    def test_plain_text_and_empty_unchanged(self):
        for text in ("", "plain text", "naïve café \U0001F600", "\\*`[]"):
            with self.subTest(text=text):
                self.assertEqual(escape(text), text)


class SafeUrlTest(unittest.TestCase):
    def test_allowed_schemes_are_kept(self):
        for url in ("http://example.com", "https://example.com/a?b=c", "mailto:a@example.com"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), url)

    def test_scheme_is_case_insensitive(self):
        self.assertEqual(safe_url("HtTpS://example.com"), "HtTpS://example.com")
        self.assertEqual(safe_url("JaVaScRiPt:alert"), BLOCKED_URL)

    def test_relative_urls_are_kept(self):
        for url in ("", "docs/a.md", "/abs/path", "#section", "?q=1", "../up"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), url)

    def test_other_schemes_are_blocked(self):
        for url in ("javascript:alert", "vbscript:x", "data:text/html,x", "file:///etc", "tel:1"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), "#")

    def test_whitespace_and_controls_in_the_scheme_are_ignored(self):
        # Browsers drop these, so "java\tscript:" is javascript: to them.
        for url in ("java\tscript:x", " javascript:x", "java\nscript:x", "\x01javascript:x",
                    "javascript\x7f:x"):
            with self.subTest(url=url):
                self.assertEqual(safe_url(url), BLOCKED_URL)
        self.assertEqual(safe_url(" http:x"), " http:x")

    def test_colon_makes_a_scheme_even_in_a_path(self):
        # The plan's rule: the scheme is the text before the first ":" (ADR consequences).
        self.assertEqual(safe_url("/a?t=10:30"), BLOCKED_URL)
        self.assertEqual(safe_url(":x"), BLOCKED_URL)

    def test_url_is_returned_unescaped(self):
        # Escaping is the caller's job, so it is not done twice.
        self.assertEqual(safe_url('https://x/?a=1&b="2"'), 'https://x/?a=1&b="2"')

    def test_allowlist_is_exactly_http_https_mailto(self):
        self.assertEqual(html.ALLOWED_SCHEMES, {"http", "https", "mailto"})
        self.assertEqual(html.BLOCKED_URL, "#")


if __name__ == "__main__":
    unittest.main()
