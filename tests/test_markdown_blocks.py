"""Tests for textkit/markdown/blocks.py: lines and blocks (plan task T3.5).

``split_lines`` and ``parse_blocks`` are tested directly; block text stays raw here (inline
Markdown is rendered by ``inlines``, tested in tests/test_markdown_inlines.py).
"""

import unittest

from textkit.markdown.blocks import (
    CodeBlock,
    Heading,
    ListBlock,
    Paragraph,
    Quote,
    Rule,
    parse_blocks,
    split_lines,
)


class SplitLinesTest(unittest.TestCase):
    def test_three_line_endings(self):
        self.assertEqual(split_lines("a\nb\r\nc\rd"), ["a", "b", "c", "d"])

    def test_final_ending_does_not_add_a_line(self):
        for text in ("a", "a\n", "a\r\n", "a\r"):
            with self.subTest(text=text):
                self.assertEqual(split_lines(text), ["a"])
        self.assertEqual(split_lines(""), [])
        self.assertEqual(split_lines("\n"), [""])
        self.assertEqual(split_lines("a\n\n"), ["a", ""])

    def test_crlf_is_one_ending_and_lf_cr_is_two(self):
        self.assertEqual(split_lines("a\r\n\r\nb"), ["a", "", "b"])
        self.assertEqual(split_lines("a\n\rb"), ["a", "", "b"])

    def test_other_separators_do_not_end_a_line(self):
        # Unlike str.splitlines.
        self.assertEqual(split_lines("a\x0cb\x85c d"), ["a\x0cb\x85c d"])


class ParseBlocksTest(unittest.TestCase):
    def test_empty_and_blank_text(self):
        for text in ("", "\n", "  \t\n\r\n", " "):
            with self.subTest(text=text):
                self.assertEqual(parse_blocks(text), [])

    def test_headings(self):
        self.assertEqual(
            parse_blocks("# One\n###### Six  \n# \n####### x\n#x"),
            [
                Heading(1, "One"),
                Heading(6, "Six"),
                Heading(1, ""),
                # Seven "#" or no space: paragraph text, and it continues the paragraph.
                Paragraph("####### x #x"),
            ],
        )

    def test_paragraphs_join_stripped_lines(self):
        self.assertEqual(
            parse_blocks("  a  \n\tb  c\n\n\nd"), [Paragraph("a b  c"), Paragraph("d")]
        )

    def test_rule(self):
        self.assertEqual(parse_blocks("---\n---  "), [Rule(), Rule()])
        self.assertEqual(parse_blocks("----\n -- -"), [Paragraph("---- -- -")])

    def test_lists_and_continuation(self):
        self.assertEqual(
            parse_blocks("- a\n  b\n    c\n* d\n-\n\n1. x\n22. y\n   z"),
            [
                ListBlock(False, ("a b c", "d")),
                # "-" alone is not an item: it ends the list and is a paragraph.
                Paragraph("-"),
                ListBlock(True, ("x", "y z")),
            ],
        )

    def test_list_ends_at_another_kind_or_unindented_text(self):
        self.assertEqual(
            parse_blocks("- a\n1. b\nc\n- d\n # e"),
            [
                ListBlock(False, ("a",)),
                ListBlock(True, ("b",)),
                Paragraph("c"),
                # One space of indent is not a continuation, and not a heading either.
                ListBlock(False, ("d",)),
                Paragraph("# e"),
            ],
        )

    def test_indented_marker_is_item_text(self):
        # One level only: a nested item continues its parent.
        self.assertEqual(parse_blocks("- a\n  - b"), [ListBlock(False, ("a - b",))])

    def test_empty_item(self):
        self.assertEqual(parse_blocks("- \n  b"), [ListBlock(False, ("b",))])
        self.assertEqual(parse_blocks("1. "), [ListBlock(True, ("",))])

    def test_fenced_code(self):
        self.assertEqual(
            parse_blocks("```python extra\n  x = 1\n\n# not a heading\n```\nafter"),
            [CodeBlock("python", ("  x = 1", "", "# not a heading")), Paragraph("after")],
        )
        self.assertEqual(parse_blocks("```\n```"), [CodeBlock(None, ())])

    def test_unclosed_fence_runs_to_the_end(self):
        self.assertEqual(
            parse_blocks("```js\na\n\n``` no\n"), [CodeBlock("js", ("a", "", "``` no"))]
        )

    def test_code_lines_drop_their_endings(self):
        self.assertEqual(
            parse_blocks("```\r\na\r\n\rb\r\n```\r\n"), [CodeBlock(None, ("a", "", "b"))]
        )

    def test_quotes_hold_paragraphs_only(self):
        self.assertEqual(
            parse_blocks(">a\n> b\n>\n>  - c\n> ```\n\n> d\nnext"),
            [
                Quote(("a b", "- c ```")),
                Quote(("d",)),
                Paragraph("next"),
            ],
        )
        self.assertEqual(parse_blocks(">"), [Quote(())])

    def test_blocks_interrupt_a_paragraph(self):
        self.assertEqual(
            parse_blocks("a\n# h\nb\n- i\nc\n2. j\nd\n> q\ne\n---\nf\n```\ng\n```"),
            [
                Paragraph("a"),
                Heading(1, "h"),
                Paragraph("b"),
                ListBlock(False, ("i",)),
                Paragraph("c"),
                ListBlock(True, ("j",)),
                Paragraph("d"),
                Quote(("q",)),
                Paragraph("e"),
                Rule(),
                Paragraph("f"),
                CodeBlock(None, ("g",)),
            ],
        )

    def test_markers_count_at_line_start_only(self):
        self.assertEqual(
            parse_blocks(" # a\n - b\n > c\n ```"), [Paragraph("# a - b > c ```")]
        )


if __name__ == "__main__":
    unittest.main()
