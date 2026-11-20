"""Tests for ``textkit/markdown/blocks.py``: line splitting and block structure (plan task T3.5).

The block parser is tested on its own output (``Heading``, ``Paragraph``, ...), without
inline parsing or HTML, so a failure here points at the block rules of the Markdown ADR
(docs/decisions/*-markdown-subset-raw-html-and-link-schemes.md).
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
    def test_every_line_ending(self):
        self.assertEqual(split_lines("a\nb\r\nc\rd"), ["a", "b", "c", "d"])

    def test_crlf_is_one_ending_and_cr_lf_reversed_is_two(self):
        self.assertEqual(split_lines("a\r\nb"), ["a", "b"])
        self.assertEqual(split_lines("a\n\rb"), ["a", "", "b"])

    def test_final_ending_does_not_add_a_line(self):
        self.assertEqual(split_lines(""), [])
        self.assertEqual(split_lines("a\n"), ["a"])
        self.assertEqual(split_lines("a\n\n"), ["a", ""])
        self.assertEqual(split_lines("\n"), [""])

    def test_other_separators_are_not_line_endings(self):
        # str.splitlines would split on these; the plan's rule does not.
        self.assertEqual(split_lines("a\x0cb\x85c d"), ["a\x0cb\x85c d"])


class ParseBlocksTest(unittest.TestCase):
    def test_empty_and_blank_text(self):
        self.assertEqual(parse_blocks(""), [])
        self.assertEqual(parse_blocks("  \n\t\n"), [])

    def test_headings(self):
        self.assertEqual(
            parse_blocks("# One\n###### Six  \n####### seven\n#none"),
            [Heading(1, "One"), Heading(6, "Six"), Paragraph("####### seven #none")],
        )
        self.assertEqual(parse_blocks("# "), [Heading(1, "")])

    def test_paragraph_lines_are_stripped_and_joined_by_one_space(self):
        self.assertEqual(
            parse_blocks("  one  \n\ttwo\n   three"), [Paragraph("one two three")]
        )

    def test_blank_line_separates_paragraphs(self):
        self.assertEqual(parse_blocks("a\n \nb"), [Paragraph("a"), Paragraph("b")])

    def test_unordered_list_with_continuation_lines(self):
        self.assertEqual(
            parse_blocks("- a\n  more\n    still\n* b\n-  c  "),
            [ListBlock(False, ("a more still", "b", "c"))],
        )

    def test_ordered_list_numbers_are_not_checked(self):
        self.assertEqual(
            parse_blocks("3. a\n1. b\n10. c"), [ListBlock(True, ("a", "b", "c"))]
        )

    def test_list_is_one_level(self):
        # An indented marker continues the item: there are no nested lists.
        self.assertEqual(parse_blocks("- a\n  - b"), [ListBlock(False, ("a - b",))])

    def test_what_ends_a_list(self):
        self.assertEqual(
            parse_blocks("- a\n\n- b\ntext\n1. c\n- d"),
            [
                ListBlock(False, ("a",)),
                ListBlock(False, ("b",)),
                Paragraph("text"),
                ListBlock(True, ("c",)),
                ListBlock(False, ("d",)),
            ],
        )

    def test_list_markers_need_a_space_and_the_first_column(self):
        self.assertEqual(
            parse_blocks("-a\n\n1.b\n\n **x**\n\n - y"),
            [Paragraph("-a"), Paragraph("1.b"), Paragraph("**x**"), Paragraph("- y")],
        )
        self.assertEqual(parse_blocks("- "), [ListBlock(False, ("",))])

    def test_fenced_code_keeps_lines_as_they_are(self):
        self.assertEqual(
            parse_blocks("```python extra\n  x = 1\t\n\n# not a heading\n```\nafter"),
            [
                CodeBlock("python", ("  x = 1\t", "", "# not a heading")),
                Paragraph("after"),
            ],
        )

    def test_fence_without_language_and_unclosed_fence(self):
        self.assertEqual(parse_blocks("```\n```"), [CodeBlock(None, ())])
        self.assertEqual(parse_blocks("```  \na\n\n"), [CodeBlock(None, ("a", ""))])

    def test_what_is_not_a_fence(self):
        self.assertEqual(
            parse_blocks("````\n\n```a`b\n\n ```"),
            [Paragraph("````"), Paragraph("```a`b"), Paragraph("```")],
        )
        # A closing fence may have trailing spaces, but not text.
        self.assertEqual(parse_blocks("```\n``` x\n```  "), [CodeBlock(None, ("``` x",))])

    def test_quote_holds_paragraphs_only(self):
        self.assertEqual(
            parse_blocks(">a\n> b\n>\n>   # c\n> - d"),
            [Quote(("a b", "# c - d"))],
        )

    def test_what_ends_a_quote(self):
        self.assertEqual(
            parse_blocks("> a\n\n> b\nc"),
            [Quote(("a",)), Quote(("b",)), Paragraph("c")],
        )
        self.assertEqual(parse_blocks(">"), [Quote(())])

    def test_rule(self):
        self.assertEqual(parse_blocks("---\n--- \n----"), [Rule(), Rule(), Paragraph("----")])

    def test_what_interrupts_a_paragraph(self):
        for line, block in (
            ("# h", Heading(1, "h")),
            ("- i", ListBlock(False, ("i",))),
            ("1. i", ListBlock(True, ("i",))),
            ("```", CodeBlock(None, ())),
            ("> q", Quote(("q",))),
            ("---", Rule()),
        ):
            with self.subTest(line=line):
                self.assertEqual(parse_blocks(f"para\n{line}"), [Paragraph("para"), block])

    def test_indented_markers_continue_a_paragraph(self):
        self.assertEqual(
            parse_blocks("para\n # h\n  > q\n ---"), [Paragraph("para # h > q ---")]
        )


if __name__ == "__main__":
    unittest.main()
