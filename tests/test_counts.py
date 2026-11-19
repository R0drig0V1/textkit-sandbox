"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import char_freq, word_count

# The case table of ADR 0002 (docs/decisions/0002-what-counts-as-a-word.md), row by row:
# (row number, input, count). Keep it in sync with the ADR; T1.10 checks the same rows
# against the words tokenizer.
WORD_COUNT_CASES = [
    (1, "", 0),
    (2, "hello", 1),
    (3, "Hello, world!", 2),
    (4, "well-known", 1),
    (5, "state-of-the-art design", 2),
    (6, "well--known", 2),
    (7, "a - b", 2),
    (8, "-5 and 5-", 3),
    (9, "COVID-19", 1),
    (10, "42", 1),
    (11, "3.14", 1),
    (12, "1,000,000", 1),
    (13, "v2.0.1", 1),
    (14, "1, 2", 2),
    (15, "a,b", 2),
    (16, "don't", 1),
    (17, "O’Brien", 1),
    (18, "rock 'n' roll", 3),
    (19, "the students' books", 3),
    (20, "e.g. this", 2),
    (21, "wait...what", 2),
    (22, "snake_case", 2),
    (23, "pages 10–20", 3),
    (24, "yes—no", 2),
    (25, "AT&T", 2),
    (26, "user@example.com", 2),
    (27, "!!! ... ?", 0),
    (28, "  one \n\n two\t three  ", 3),
    (29, " \n\t ", 0),
    (30, "naïve café", 2),
    (31, "naïve café", 2),
    (32, "́abc", 1),
    (33, "हिन्दी", 1),
    (34, "東京 2026", 2),
    (35, "x²", 1),
]


class WordCountTest(unittest.TestCase):
    def test_adr_0002_case_table(self):
        for row, text, expected in WORD_COUNT_CASES:
            with self.subTest(row=row, text=text):
                self.assertEqual(word_count(text), expected)

    def test_case_table_rows_are_numbered_in_order(self):
        # Guards against a row being dropped or duplicated when the table is edited.
        self.assertEqual([row for row, _, _ in WORD_COUNT_CASES],
                         list(range(1, len(WORD_COUNT_CASES) + 1)))


class CharFreqTest(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(char_freq(""), {})

    def test_whitespace_only(self):
        self.assertEqual(char_freq(" \t\n\r\x0b\x0c"), {})

    def test_counts_each_character(self):
        self.assertEqual(char_freq("hello"), {"h": 1, "e": 1, "l": 2, "o": 1})

    def test_keys_in_order_of_first_occurrence(self):
        result = char_freq("banana split")
        self.assertEqual(list(result), ["b", "a", "n", "s", "p", "l", "i", "t"])
        self.assertEqual(result, {"b": 1, "a": 3, "n": 2, "s": 1, "p": 1, "l": 1,
                                  "i": 1, "t": 1})

    def test_order_is_not_alphabetical_or_by_count(self):
        # "z" comes first although it is last alphabetically and the least frequent.
        self.assertEqual(list(char_freq("zaab")), ["z", "a", "b"])

    def test_case_sensitive(self):
        result = char_freq("aAa")
        self.assertEqual(result, {"a": 2, "A": 1})
        self.assertEqual(list(result), ["a", "A"])

    def test_spaces_tabs_newlines_are_not_counted(self):
        self.assertEqual(char_freq(" a\tb\n a \r\n"), {"a": 2, "b": 1})

    def test_unicode_whitespace_is_not_counted(self):
        # NO-BREAK SPACE, EM SPACE, LINE SEPARATOR, IDEOGRAPHIC SPACE: all str.isspace().
        self.assertEqual(char_freq("a\u00a0b\u2003c\u2028d\u3000e"),
                         {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1})

    def test_punctuation_digits_and_symbols_are_counted(self):
        self.assertEqual(char_freq("1+1=2!"), {"1": 2, "+": 1, "=": 1, "2": 1, "!": 1})

    def test_non_ascii_characters(self):
        self.assertEqual(char_freq("Ñandú ñ"), {"Ñ": 1, "a": 1, "n": 1, "d": 1, "ú": 1,
                                                "ñ": 1})

    def test_no_normalization(self):
        # NFC "é" is one code point; NFD is "e" + U+0301, counted as two keys.
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})

    def test_returns_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)


if __name__ == "__main__":
    unittest.main()
