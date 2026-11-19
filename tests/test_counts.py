"""Tests for textkit.counts. One TestCase class per public function."""

import unittest

from textkit.counts import char_freq, reading_time, word_count

# Every row of the case table in docs/decisions/0001-what-counts-as-a-word.md, in the same
# order and with the same literals. Keep the two in sync: T1.10 tests its tokenizer against
# the same table.
WORD_COUNT_CASES = [
    ("", 0),
    ("  \n\t  ", 0),
    ("... !!! ?", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("one  two\n\nthree\tfour", 4),
    ("well-known", 1),
    ("state-of-the-art", 1),
    ("well - known", 2),
    ("-leading trailing-", 2),
    ("a--b", 2),
    ("word—word", 2),
    ("don't", 1),
    ("don’t", 1),
    ("rock'n'roll", 1),
    ("'quoted'", 1),
    ("dogs' bowls", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("1, 2, 3", 3),
    ("v2.0", 1),
    ("end.Start", 2),
    ("e.g.", 2),
    ("snake_case", 2),
    ("naïve café", 2),
    ("Ñandú", 1),
    ("日本語", 1),
    ("C++ and C#", 3),
    ("50%", 1),
    ("-5", 1),
]


class WordCountTest(unittest.TestCase):
    def test_adr_0001_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_nfc_and_nfd_count_the_same(self):
        # Rule 2 of ADR 0001: combining marks must not split a word.
        self.assertEqual(word_count("Ñandú es"), word_count("Ñandú es"))

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            word_count(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            word_count(["a", "b"])  # type: ignore[arg-type]


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("hello"), {"h": 1, "e": 1, "l": 2, "o": 1})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n\r\f\v\u00a0\u2003"), {})

    def test_whitespace_is_not_counted(self):
        self.assertEqual(char_freq("a b\tc\na\u00a0b"), {"a": 2, "b": 2, "c": 1})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("banana split")), ["b", "a", "n", "s", "p", "l", "i", "t"])

    def test_punctuation_digits_and_non_ascii_are_counted(self):
        self.assertEqual(char_freq("ñ1!ñ"), {"ñ": 2, "1": 1, "!": 1})

    def test_no_normalization(self):
        # NFD "ú" is two code points: "u" and U+0301 COMBINING ACUTE ACCENT.
        self.assertEqual(char_freq("u\u0301"), {"u": 1, "\u0301": 1})
        self.assertEqual(char_freq("\u00fa"), {"\u00fa": 1})

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            char_freq(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            char_freq(["a"])  # type: ignore[arg-type]


class ReadingTimeTest(unittest.TestCase):
    # Cases of docs/decisions/0004-reading-time-rounds-up.md: (text, wpm, minutes).
    CASES = [
        ("", 200, 0),
        ("  \n\t ", 200, 0),
        ("... !!! ?", 200, 0),
        ("hello", 200, 1),
        (" ".join(["w"] * 199), 200, 1),
        (" ".join(["w"] * 200), 200, 1),
        (" ".join(["w"] * 201), 200, 2),
        (" ".join(["w"] * 400), 200, 2),
        (" ".join(["w"] * 401), 200, 3),
        ("one two three", 1, 3),
        ("one two three", 2, 2),
    ]

    def test_adr_0004_cases(self):
        for text, wpm, expected in self.CASES:
            with self.subTest(words=word_count(text), wpm=wpm):
                self.assertEqual(reading_time(text, wpm), expected)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time(" ".join(["w"] * 200)), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 201)), 2)

    def test_counts_words_with_word_count(self):
        # "well-known" and "3.14" are one word each under ADR 0001: 2 words at 1 wpm.
        self.assertEqual(reading_time("well-known 3.14", wpm=1), 2)

    def test_large_counts_are_exact(self):
        # Integer ceiling division: no float error at an exact multiple of wpm.
        text = " ".join(["w"] * 10_000)
        self.assertEqual(reading_time(text, wpm=3), 3334)
        self.assertEqual(reading_time(text, wpm=10_000), 1)

    def test_wpm_below_one_raises(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm), self.assertRaises(ValueError):
                reading_time("hello", wpm)
        # Even for text with no words: the argument is invalid either way.
        with self.assertRaises(ValueError):
            reading_time("", 0)

    def test_rejects_non_int_wpm(self):
        for wpm in (200.0, "200", None, True):
            with self.subTest(wpm=wpm), self.assertRaises(TypeError):
                reading_time("hello", wpm)  # type: ignore[arg-type]

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            reading_time(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            reading_time(["a", "b"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
