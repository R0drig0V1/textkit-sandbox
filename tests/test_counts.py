"""Tests for textkit.counts.

The word rule is tested against the example table of ADR 0001, read from the ADR itself,
so the documented examples and the code cannot drift apart. T1.10's shared tokenizer can
run the same table against ``textkit._tokens.words``.
"""

import ast
import pathlib
import re
import unittest

from textkit.counts import _words, word_count

ADR = pathlib.Path(__file__).resolve().parent.parent / "docs/decisions/0001-what-counts-as-a-word.md"

# One example row: | `<str literal>` | `<list literal>` | <count> |
_ROW = re.compile(r"^\| `(.+?)` \| `(\[.*?\])` \| (\d+) \|$", re.M)


def adr_examples():
    """Return (text, words, count) for every row of the ADR 0001 example table."""
    return [
        (ast.literal_eval(text), ast.literal_eval(words), int(count))
        for text, words, count in _ROW.findall(ADR.read_text(encoding="utf-8"))
    ]


class AdrExamplesTest(unittest.TestCase):
    def test_table_is_read(self):
        # Guards against a reformatted table silently matching no rows.
        self.assertGreaterEqual(len(adr_examples()), 40)

    def test_every_example(self):
        for text, words, count in adr_examples():
            with self.subTest(text=text):
                self.assertEqual(len(words), count, "the ADR row contradicts itself")
                self.assertEqual(_words(text), words)
                self.assertEqual(word_count(text), count)


class WordCountTest(unittest.TestCase):
    def test_composed_and_decomposed_accents_count_the_same(self):
        self.assertEqual(word_count("café crème"), word_count("café crème"))

    def test_any_whitespace_separates(self):
        self.assertEqual(word_count("a b　c\r\nd"), 4)

    def test_mark_after_a_joiner_does_not_join(self):
        # A joiner needs a letter or digit right after it; a mark is not enough.
        self.assertEqual(_words("a-́b"), ["a", "b"])

    def test_str_subclass_is_accepted(self):
        class Text(str):
            pass

        self.assertEqual(word_count(Text("two words")), 2)

    def test_non_str_raises_type_error(self):
        for value in (None, b"bytes", 42, ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)


if __name__ == "__main__":
    unittest.main()
