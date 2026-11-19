"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import word_count

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


if __name__ == "__main__":
    unittest.main()
