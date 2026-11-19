"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import math
import pathlib
import re
import unittest

from textkit.counts import char_freq, reading_time, sentence_count, word_count

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


def _n_words(n):
    """Return ``n`` copies of "word" separated by single spaces (ADR 0004's "n words")."""
    return " ".join(["word"] * n)


# The case table of ADR 0004 (docs/decisions/0004-reading-time-rounds-up.md), row by row:
# (row number, text, wpm, minutes). Keep it in sync with the ADR.
READING_TIME_CASES = [
    (1, "", 200, 0),
    (2, " \n\t ", 200, 0),
    (3, "!!! ... ?", 200, 0),
    (4, "- " * 500, 200, 0),
    (5, "hello", 200, 1),
    (6, _n_words(199), 200, 1),
    (7, _n_words(200), 200, 1),
    (8, _n_words(201), 200, 2),
    (9, _n_words(400), 200, 2),
    (10, _n_words(401), 200, 3),
    (11, "well-known " * 201, 200, 2),
    (12, "one two three", 1, 3),
    (13, "one two three", 2, 2),
    (14, "a b", 1000, 1),
    (15, "", 1, 0),
]

# The error table of ADR 0004: (text, wpm, exception).
READING_TIME_ERRORS = [
    ("hello", 0, ValueError),
    ("hello", -5, ValueError),
    ("", 0, ValueError),
    ("hello", 0.5, ValueError),
    ("hello", 200.0, TypeError),
    ("hello", True, TypeError),
]


class ReadingTimeTest(unittest.TestCase):
    def test_adr_0004_case_table(self):
        for row, text, wpm, expected in READING_TIME_CASES:
            with self.subTest(row=row, text=text[:20], wpm=wpm):
                self.assertEqual(reading_time(text, wpm), expected)

    def test_case_table_rows_are_numbered_in_order(self):
        self.assertEqual([row for row, _, _, _ in READING_TIME_CASES],
                         list(range(1, len(READING_TIME_CASES) + 1)))

    def test_adr_0004_error_table(self):
        for text, wpm, error in READING_TIME_ERRORS:
            with self.subTest(text=text, wpm=wpm):
                with self.assertRaises(error):
                    reading_time(text, wpm)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time(_n_words(200)), 1)
        self.assertEqual(reading_time(_n_words(201)), 2)

    def test_returns_an_int(self):
        self.assertIs(type(reading_time("hello")), int)

    def test_matches_ceiling_of_word_count(self):
        # Cross-check the integer formula against the float definition on small inputs,
        # where float division is exact enough to compare.
        for words in range(0, 60):
            for wpm in range(1, 25):
                with self.subTest(words=words, wpm=wpm):
                    expected = math.ceil(words / wpm)
                    self.assertEqual(reading_time(_n_words(words), wpm), expected)


# The case table of ADR 0005 (docs/decisions/0005-sentence-boundaries.md), row by row:
# (row number, input, count). test_matches_the_adr_table keeps it in sync with the ADR.
SENTENCE_COUNT_CASES = [
    (1, "", 0),
    (2, " \n\t ", 0),
    (3, "Hello world", 1),
    (4, "Hello.", 1),
    (5, "Hello. World.", 2),
    (6, "Hello.\nWorld.", 2),
    (7, "Title\n\nBody text.", 1),
    (8, "Really?! Yes.", 2),
    (9, "Hi!!!   ", 1),
    (10, "!!! ... ?", 0),
    (11, "I met Dr. Smith. He was kind.", 2),
    (12, "Mr. and Mrs. Smith arrived.", 1),
    (13, "DR. NO is a film.", 1),
    (14, "Use a list, e.g. Python lists.", 1),
    (15, "Fruit, i.e. apples. Done.", 2),
    (16, "Apples, pears, etc. Then we left.", 2),
    (17, "Apples, pears, etc. and more.", 1),
    (18, "Wait... what?", 1),
    (19, "Wait... What?", 2),
    (20, "Wait… What?", 2),
    (21, "wait...what", 1),
    (22, "...and then it ended.", 1),
    (23, "Dr.. Smith", 2),
    (24, "Pi is 3.14. Next.", 2),
    (25, "end.Next", 1),
    (26, "J. R. R. Tolkien wrote it. He died in 1973.", 2),
    (27, "I saw plan B. It worked.", 1),
    (28, "In the U.S. Then we left.", 2),
    (29, 'He said "Stop." Then he left.', 2),
    (30, '"Stop!" he said.', 1),
    (31, "(See Dr. Who.) Then more.", 2),
    (32, "It costs $5. Fine.", 2),
    (33, "¿Qué? ¡Sí!", 2),
    (34, "Привет. Как дела?", 2),
    (35, "東京。大阪。", 1),
]

SENTENCE_ADR = (pathlib.Path(__file__).resolve().parents[1]
                / "docs" / "decisions" / "0005-sentence-boundaries.md")


class SentenceCountTest(unittest.TestCase):
    def test_adr_0005_case_table(self):
        for row, text, expected in SENTENCE_COUNT_CASES:
            with self.subTest(row=row, text=text):
                self.assertEqual(sentence_count(text), expected)

    def test_case_table_rows_are_numbered_in_order(self):
        # Guards against a row being dropped or duplicated when the table is edited.
        self.assertEqual([row for row, _, _ in SENTENCE_COUNT_CASES],
                         list(range(1, len(SENTENCE_COUNT_CASES) + 1)))

    def test_matches_the_adr_table(self):
        # The ADR is the spec: its table rows, read as Python literals, must equal the list
        # above, so neither can change without the other.
        rows = re.findall(r"^\| (\d+) \| `(.+?)` \| (\d+) \|", SENTENCE_ADR.read_text(), re.M)
        self.assertEqual([(int(n), ast.literal_eval(s), int(c)) for n, s, c in rows],
                         SENTENCE_COUNT_CASES)

    def test_every_listed_abbreviation_in_any_case(self):
        # ADR 0005, rule 3: each listed abbreviation keeps the sentence going before a capital.
        for abbr in ["Mr", "Mrs", "Ms", "Mx", "Dr", "Prof", "vs", "cf", "e.g", "i.e"]:
            for form in (abbr, abbr.upper(), abbr.lower()):
                with self.subTest(form=form):
                    self.assertEqual(sentence_count(f"See {form}. Smith now. Done."), 2)

    def test_closers_after_a_terminator(self):
        # ADR 0005, rule 1: every closer may sit between the run and the whitespace.
        for closer in "\"'”’»)]}":
            with self.subTest(closer=closer):
                self.assertEqual(sentence_count(f"One.{closer} Two."), 2)

    def test_terminator_at_end_of_text_after_abbreviation(self):
        # The last piece counts with or without a boundary, so a final "Dr." is still one.
        self.assertEqual(sentence_count("Call the Dr."), 1)

    def test_returns_int(self):
        self.assertIs(type(sentence_count("A. B.")), int)


if __name__ == "__main__":
    unittest.main()
