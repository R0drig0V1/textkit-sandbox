"""Tests for textkit.counts, one TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, reading_time, sentence_count, word_count

# The table of cases that ends the ADR "What counts as a word", row by row, in order.
# test_cases_match_the_adr_table keeps the two in sync.
WORD_COUNT_CASES = [
    ("", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("!!! ... ?", 0),
    ("  one \n\n two\t three  ", 3),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a -- b", 2),
    ("a--b", 2),
    ("-leading trailing-", 2),
    ("don't", 1),
    ("it’s", 1),
    ("'quoted'", 1),
    ("the dogs' bones", 3),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("-5", 1),
    ("COVID-19", 1),
    ("end.Start", 2),
    ("e.g.", 2),
    ("1/2", 2),
    ("snake_case", 2),
    ("naïve café", 2),
    ("naïve", 1),
    ("日本語", 1),
]

# Found by title, not number: the integrator may renumber the ADR at merge.
_DECISIONS = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions"
_ROW = re.compile(r"^\| `(.+)` \| (\d+) \|", re.M)


def _adr_cases() -> list[tuple[str, int]]:
    """Return the (input, count) rows of the word ADR's case table."""
    (adr,) = _DECISIONS.glob("[0-9][0-9][0-9][0-9]-what-counts-as-a-word.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    return [(ast.literal_eval(text), int(count)) for text, count in _ROW.findall(table)]


class WordCountTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_joiner_at_the_very_end(self):
        # The lookahead must not run past the end of the text.
        self.assertEqual(word_count("well-"), 1)
        self.assertEqual(word_count("3."), 1)

    def test_mixed_sentence(self):
        text = "It's a well-known fact: 3.14 isn't exactly π -- or is it?"
        self.assertEqual(word_count(text), 11)

    def test_rejects_non_str(self):
        for value in (b"two words", ["two", "words"], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)  # type: ignore[arg-type]


class CharFreqTest(unittest.TestCase):
    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \t\n\r\f\v\u00a0\u2003\u3000"), {})

    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_whitespace_skipped_punctuation_counted(self):
        self.assertEqual(
            char_freq("a b,\tb!\n"), {"a": 1, "b": 2, ",": 1, "!": 1}
        )

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("cabbage")), ["c", "a", "b", "g", "e"])

    def test_non_ascii_per_code_point(self):
        self.assertEqual(char_freq("日本日"), {"日": 2, "本": 1})
        # No normalization: NFD "é" is "e" plus U+0301, counted separately.
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})

    def test_rejects_non_str(self):
        for value in (b"abc", ["a", "b"], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)  # type: ignore[arg-type]


class ReadingTimeTest(unittest.TestCase):
    # The table of cases that ends the ADR "Reading time rounding": (words, wpm, minutes).
    ADR_CASES = [
        (0, 200, 0),
        (1, 200, 1),
        (199, 200, 1),
        (200, 200, 1),
        (201, 200, 2),
        (400, 200, 2),
        (401, 200, 3),
        (5, 1, 5),
    ]

    def test_adr_table(self):
        for words, wpm, expected in self.ADR_CASES:
            with self.subTest(words=words, wpm=wpm):
                self.assertEqual(reading_time(" ".join(["word"] * words), wpm), expected)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time("word " * 200), 1)
        self.assertEqual(reading_time("word " * 201), 2)

    def test_no_words_is_zero_minutes(self):
        for text in ("", "   \n\t ", "!!! ... ?"):
            with self.subTest(text=text):
                self.assertEqual(reading_time(text), 0)

    def test_counts_words_with_word_count(self):
        # 3 words by the word rule ("--" and "!!!" are not words), though str.split()
        # sees 5 tokens: 5 words at 3 wpm would give 2 minutes, not 1.
        text = "well-known -- don't stop !!!"
        self.assertEqual(word_count(text), 3)
        self.assertEqual(reading_time(text, wpm=3), 1)
        self.assertEqual(reading_time(text, wpm=2), 2)

    def test_rejects_wpm_below_one(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("hello", wpm)
        # Even when the text has no words.
        with self.assertRaises(ValueError):
            reading_time("", 0)

    def test_rejects_non_int_wpm(self):
        for wpm in (200.0, "200", None, True):
            with self.subTest(wpm=wpm):
                with self.assertRaises(TypeError):
                    reading_time("hello", wpm)  # type: ignore[arg-type]

    def test_rejects_non_str(self):
        for value in (b"two words", ["two", "words"], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    reading_time(value)  # type: ignore[arg-type]


class SentenceCountTest(unittest.TestCase):
    # The table of cases that ends the ADR "Sentence boundaries: abbreviations and
    # ellipses", row by row, in order. test_cases_match_the_adr_table keeps the two in sync.
    ADR_CASES = [
        ("", 0),
        ("Hello world", 1),
        ("Hello. World.", 2),
        ("Really?! Yes!!!", 2),
        ("!!! ... ?", 0),
        ("One.  Two.\nThree.", 3),
        ("Dr. Smith arrived. He sat down.", 2),
        ("Mr. and Mrs. Smith left.", 1),
        ("DR. Who? Prof. X.", 2),
        ("Take fruit, e.g. an apple. Or a pear.", 2),
        ("Fruit, i.e. apples, e.g. Fuji, is sweet.", 1),
        ("(e.g. this) works.", 1),
        ("Ask the Dr.", 1),
        ("Apples, pears, etc. are fruit.", 1),
        ("Apples, pears, etc. Then bread.", 2),
        ("Wait... what?", 1),
        ("I wonder... Maybe tomorrow.", 2),
        ("Wait… what?", 1),
        ('He paused... "maybe" not.', 1),
        ("Well...", 1),
        ("What?... No.", 2),
        ("Pi is 3.14. It never ends.", 2),
        ("Visit example.com today.", 1),
        ('He said "Stop." Then he left.', 2),
        ("(It rained.) We stayed in.", 2),
        ("He lives on Main St. He likes it.", 1),
        ("The U.S. Army won.", 2),
        ("J. Smith wrote it.", 2),
        ("Wait . . . what", 2),
    ]

    @staticmethod
    def _adr_cases() -> list[tuple[str, int]]:
        """Return the (input, count) rows of the sentence ADR's case table, found by title."""
        (adr,) = _DECISIONS.glob("[0-9][0-9][0-9][0-9]-sentence-abbreviations-and-ellipses.md")
        table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
        return [(ast.literal_eval(text), int(count)) for text, count in _ROW.findall(table)]

    def test_adr_table(self):
        for text, expected in self.ADR_CASES:
            with self.subTest(text=text):
                self.assertEqual(sentence_count(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(self._adr_cases(), self.ADR_CASES)

    def test_every_listed_abbreviation(self):
        for abbr in ("Mr", "Mrs", "Ms", "Dr", "Prof", "St", "vs", "cf", "e.g", "i.e"):
            with self.subTest(abbr=abbr):
                self.assertEqual(sentence_count(f"See {abbr}. Next word."), 1)
                # The same token without its dot is an ordinary word before a period.
                self.assertEqual(sentence_count(f"See {abbr}! Next word."), 2)

    def test_unlisted_word_before_a_period_ends_a_sentence(self):
        # "Drs" and "Doctor" look like "Dr" but are not listed.
        self.assertEqual(sentence_count("Ask the Drs. They know."), 2)
        self.assertEqual(sentence_count("Ask the Doctor. She knows."), 2)

    def test_two_dots_are_an_ellipsis(self):
        self.assertEqual(sentence_count("Hmm.. okay."), 1)
        self.assertEqual(sentence_count("Hmm.. Okay."), 2)

    def test_ellipsis_before_a_digit_or_caseless_word_ends_a_sentence(self):
        self.assertEqual(sentence_count("Wait... 3 more."), 2)
        self.assertEqual(sentence_count("Wait... 日本語."), 2)

    def test_closers_at_the_very_end(self):
        # The scan past closing quotes must not run past the end of the text.
        self.assertEqual(sentence_count('"Stop."'), 1)
        self.assertEqual(sentence_count("(Done.)”"), 1)

    def test_trailing_whitespace_and_marks_add_nothing(self):
        self.assertEqual(sentence_count("Hello.   \n"), 1)
        self.assertEqual(sentence_count("Hello. ... !!"), 1)

    def test_rejects_non_str(self):
        for value in (b"One. Two.", ["One.", "Two."], None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    sentence_count(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
