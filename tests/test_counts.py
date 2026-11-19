"""Tests for textkit.counts.

The word rule is tested against the example table of ADR 0001, read from the ADR itself,
so the documented examples and the code cannot drift apart. T1.10's shared tokenizer can
run the same table against ``textkit._tokens.words``. ``char_freq`` is tested on the edges
its docstring documents: whitespace by ``str.isspace()``, case, NFC versus NFD, the type.
"""

import ast
import pathlib
import re
import unittest

from textkit.counts import _words, char_freq, word_count

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


class CharFreqTest(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(char_freq(""), {})

    def test_only_whitespace(self):
        # Every kind of whitespace str.isspace() knows: ASCII, NBSP, ideographic, line sep.
        self.assertEqual(char_freq(" \t\n\r\x0b\x0c\u00a0\u3000\u2028\x1f"), {})

    def test_spaces_inside_text_are_skipped(self):
        self.assertEqual(char_freq("a a\tb\u00a0b"), {"a": 2, "b": 2})

    def test_zero_width_space_is_counted(self):
        # U+200B is not whitespace for str.isspace(), so it is a character like any other.
        self.assertEqual(char_freq("a\u200bb"), {"a": 1, "\u200b": 1, "b": 1})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("AaA"), {"A": 2, "a": 1})

    def test_punctuation_and_digits(self):
        self.assertEqual(char_freq("a, b! 1.1"), {"a": 1, ",": 1, "b": 1, "!": 1, "1": 2, ".": 1})

    def test_non_ascii(self):
        self.assertEqual(char_freq("ñandú 日日 😀"), {"ñ": 1, "a": 1, "n": 1, "d": 1, "ú": 1, "日": 2, "😀": 1})

    def test_nfc_and_nfd_count_differently(self):
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})

    def test_keys_in_order_of_first_appearance(self):
        self.assertEqual(list(char_freq("banana")), ["b", "a", "n"])

    def test_returns_plain_dict(self):
        result = char_freq("abc")
        self.assertIs(type(result), dict)
        for key in result:
            self.assertIs(type(key), str)

    def test_str_subclass_is_accepted_and_keys_are_plain_str(self):
        class Text(str):
            pass

        result = char_freq(Text("aab"))
        self.assertEqual(result, {"a": 2, "b": 1})
        self.assertTrue(all(type(key) is str for key in result))

    def test_non_str_raises_type_error(self):
        for value in (None, b"bytes", 42, ["a", "b"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)


if __name__ == "__main__":
    unittest.main()
