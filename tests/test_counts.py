"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import char_freq, reading_time, sentence_count, word_count

# The table of cases at the end of docs/decisions/0002-what-counts-as-a-word.md, row by row
# and in the same order. Keep the two in sync.
ADR_0002_CASES = [
    ("well-known", 1),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("don't", 1),
    ("don’t", 1),
    ("the dogs' bowls", 3),
    ("'tis", 1),
    ("", 0),
    ("!!! ... ?", 0),
    ("  one \n\n two\t three  ", 3),
    ("a--b", 2),
    ("well - known", 2),
    ("snake_case", 2),
    ("U.S.A.", 3),
    ("1, 2, 3", 3),
    ("naïve café", 2),
    ("naïve café", 2),
]


class WordCountTest(unittest.TestCase):
    def test_adr_0002_table(self):
        for text, expected in ADR_0002_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_sentence(self):
        self.assertEqual(word_count("It's a well-known fact: 3.5 cats aren't 2 dogs."), 9)

    def test_joiner_at_end_of_text(self):
        self.assertEqual(word_count("pre-"), 1)
        self.assertEqual(word_count("3."), 1)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("cabbage")), ["c", "a", "b", "g", "e"])

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_whitespace_is_not_counted(self):
        # Every character here satisfies str.isspace(), including the no-break space.
        self.assertEqual(char_freq(" a\tb\nc\r\u00a0\u2003a "), {"a": 2, "b": 1, "c": 1})

    def test_punctuation_and_digits_are_counted(self):
        self.assertEqual(char_freq("1, 1!"), {"1": 2, ",": 1, "!": 1})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n "), {})

    def test_no_unicode_normalization(self):
        # NFC "é" is one code point; NFD is "e" plus a combining acute accent.
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})


# The table of cases at the end of docs/decisions/0004-reading-time-rounding.md, row by row
# and in the same order: (text, wpm, minutes). Keep the two in sync.
ADR_0004_CASES = [
    ("", 200, 0),
    ("!!! ... ?", 200, 0),
    ("word", 200, 1),
    ("w " * 199, 200, 1),
    ("w " * 200, 200, 1),
    ("w " * 201, 200, 2),
    ("w " * 400, 200, 2),
    ("w " * 401, 200, 3),
    ("one two three", 1, 3),
    ("well-known don't 3.14", 3, 1),
]


class ReadingTimeTest(unittest.TestCase):
    def test_adr_0004_table(self):
        for text, wpm, expected in ADR_0004_CASES:
            with self.subTest(text=text[:20], wpm=wpm):
                self.assertEqual(reading_time(text, wpm), expected)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time("w " * 200), 1)
        self.assertEqual(reading_time("w " * 201), 2)

    def test_counts_words_with_word_count(self):
        # "a - b" is two words under ADR 0002 but three with str.split().
        self.assertEqual(reading_time("a - b", wpm=2), 1)

    def test_returns_int(self):
        self.assertIs(type(reading_time("one two three", 2)), int)

    def test_wpm_below_one_raises(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("some words", wpm)

    def test_wpm_checked_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            reading_time("", 0)


# The table of cases at the end of docs/decisions/0005-sentence-boundaries.md, row by row
# and in the same order. Keep the two in sync.
ADR_0005_CASES = [
    ("", 0),
    ("Hello", 1),
    ("Hello world. Bye.", 2),
    ("Really?! Yes!!", 2),
    ("It costs 3.14 dollars.", 1),
    ("Visit example.com today.", 1),
    ("One.Two", 1),
    ("I met Dr. Smith. He was kind.", 2),
    ("Mr. and Mrs. Smith left.", 1),
    ("DR. NO is a film.", 1),
    ("Use a tool, e.g. a hammer.", 1),
    ("Fruit, i.e. apples, is good.", 1),
    ("Cats vs. dogs.", 1),
    ("Bring pens, paper, etc. Then sit.", 2),
    ("I live in the U.S. and it is big.", 2),
    ("Wait... what happened?", 1),
    ("I waited... Nobody came.", 2),
    ("I waited\u2026 Nobody came.", 2),
    ("The end...", 1),
    ("He said \"Stop.\" Then he left.", 2),
    ("\"Why?\" he asked.", 2),
    ("!!! ... ?", 0),
    ("Hi. ... Bye.", 2),
    ("Line one\nLine two", 1),
    ("First. \n\n Second.", 2),
]


class SentenceCountTest(unittest.TestCase):
    def test_adr_0005_table(self):
        for text, expected in ADR_0005_CASES:
            with self.subTest(text=text):
                self.assertEqual(sentence_count(text), expected)

    def test_whitespace_only(self):
        self.assertEqual(sentence_count(" \t\n "), 0)

    def test_abbreviation_must_stand_alone(self):
        # "2dr." is not the title "Dr.", so its period cuts like any other.
        self.assertEqual(sentence_count("Model 2dr. It is red."), 2)
        self.assertEqual(sentence_count("(Dr. Who) is on. Watch it."), 2)

    def test_ellipsis_before_quoted_capital(self):
        # Opening quotes are skipped when looking for the capital after an ellipsis.
        self.assertEqual(sentence_count("So... \"Yes,\" she said."), 2)
        self.assertEqual(sentence_count("So... \"yes,\" she said."), 1)

    def test_closing_bracket_after_terminator(self):
        self.assertEqual(sentence_count("It worked (mostly.) Then it broke."), 2)

    def test_run_with_question_mark_always_cuts(self):
        self.assertEqual(sentence_count("Really?... maybe not."), 2)


if __name__ == "__main__":
    unittest.main()
