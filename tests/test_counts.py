"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import time
import unittest

from textkit.counts import char_freq, reading_time, word_count
from textkit.counts import sentence_count

# The case table of docs/decisions/0002-what-counts-as-a-word.md, as (input, count). The ADR
# is the specification; WordCountTest.test_adr_table_matches keeps the two in sync.
WORD_COUNT_CASES = [
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("foo--bar", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000 people", 2),
    ("2nd place", 2),
    ("don't", 1),
    ("it’s", 1),
    ("'quoted'", 1),
    ("the dogs' bowls", 3),
    ("", 0),
    ("!?.,;:--", 0),
    ("   \n\t  ", 0),
    ("one  two\n\nthree\tfour", 4),
    ("end.Start", 2),
    ("already_snake", 2),
    ("naïve café", 2),
    ("naïve", 2),
]

_DECISIONS = pathlib.Path(__file__).resolve().parent.parent / "docs" / "decisions"


def _adr_cases() -> list:
    """Parse the case table of the word ADR into (input, count) pairs.

    Found by title rather than number, since the integrator may renumber the ADR at merge.
    """
    (adr,) = _DECISIONS.glob("*-what-counts-as-a-word.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_adr_table_matches(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_prose(self):
        self.assertEqual(word_count("Hello, world! It's a well-known fact."), 6)

    def test_non_str_raises_type_error(self):
        for value in (None, 42, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_whitespace_not_counted(self):
        # Ordinary, control and Unicode whitespace (NBSP, em space, line separator).
        self.assertEqual(char_freq("a b\tc\nd\r\x0b\x0c   e"),
                         {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("hello world")), ["h", "e", "l", "o", "w", "r", "d"])

    def test_empty_and_whitespace_only(self):
        for text in ("", "   \n\t  "):
            with self.subTest(text=text):
                self.assertEqual(char_freq(text), {})

    def test_punctuation_and_digits_counted(self):
        self.assertEqual(char_freq("a1!1!"), {"a": 1, "1": 2, "!": 2})

    def test_code_points_without_normalization(self):
        self.assertEqual(char_freq("é"), {"é": 1})
        self.assertEqual(char_freq("é"), {"e": 1, "́": 1})

    def test_returns_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)

    def test_non_str_raises_type_error(self):
        for value in (None, 42, b"bytes", ["a"]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)


class ReadingTimeTest(unittest.TestCase):
    """Rounding cases of docs/decisions/0006-reading-time-rounding.md."""

    def test_empty_and_wordless_text_is_zero(self):
        for text in ("", "   \n\t ", "!?.,;:--"):
            with self.subTest(text=text):
                self.assertEqual(reading_time(text), 0)

    def test_under_one_minute_rounds_up_to_one(self):
        self.assertEqual(reading_time("word"), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 199)), 1)

    def test_exact_minutes(self):
        self.assertEqual(reading_time(" ".join(["w"] * 200)), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 400)), 2)

    def test_partial_minute_rounds_up(self):
        self.assertEqual(reading_time(" ".join(["w"] * 201)), 2)
        self.assertEqual(reading_time(" ".join(["w"] * 399)), 2)

    def test_custom_wpm(self):
        self.assertEqual(reading_time("one two three", wpm=1), 3)
        self.assertEqual(reading_time("one two three", wpm=2), 2)
        self.assertEqual(reading_time("one two three", wpm=3), 1)

    def test_uses_word_count(self):
        # "well-known" and "3.14" are one word each under the word ADR.
        self.assertEqual(reading_time("well-known 3.14", wpm=2), 1)
        self.assertEqual(reading_time("well known 3 14", wpm=2), 2)

    def test_wpm_below_one_raises_value_error(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("text", wpm)

    def test_non_int_wpm_raises_type_error(self):
        for wpm in (200.0, "200", None, True):
            with self.subTest(wpm=wpm):
                with self.assertRaises(TypeError):
                    reading_time("text", wpm)

    def test_non_str_text_raises_type_error(self):
        for value in (None, 42, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    reading_time(value)


# The case table of docs/decisions/0007-sentence-count-abbreviations-and-ellipses.md, as
# (input, count). SentenceCountTest.test_adr_table_matches keeps the two in sync.
SENTENCE_COUNT_CASES = [
    ("", 0),
    ("   \n\t ", 0),
    ("...", 0),
    ("!?!", 0),
    ("Hello", 1),
    ("Hello world.", 1),
    ("One. Two. Three.", 3),
    ("Really?! Yes!!!", 2),
    ("Hi! !!", 1),
    ("Line one\nline two", 1),
    ("Pi is 3.14 exactly. Yes.", 2),
    ("Version 2. Next step.", 2),
    ("See Dr. Smith. He is in.", 2),
    ("Mr. and Mrs. Brown left.", 1),
    ("DR. NO. Fine.", 2),
    ("Use a tool, e.g. a hammer. Then stop.", 2),
    ("Fruit (i.e. apples) is good.", 1),
    ("It was 5 p.m. when we met.", 1),
    ("J. R. R. Tolkien wrote it.", 1),
    ("Bring pens, paper, etc. Then we start.", 1),
    ('He said "Stop." Then he left.', 2),
    ("She said “Go.” He went.", 2),
    ("Wait... what? No.", 2),
    ("I don't know... Maybe tomorrow.", 2),
    ("Well… fine.", 1),
    ("It ends with an ellipsis...", 1),
]


def _sentence_adr_cases() -> list:
    """Parse the case table of the sentence ADR into (input, count) pairs.

    Found by title rather than number, since the integrator may renumber the ADR at merge.
    """
    (adr,) = _DECISIONS.glob("*-sentence-count-abbreviations-and-ellipses.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class SentenceCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in SENTENCE_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(sentence_count(text), expected)

    def test_adr_table_matches(self):
        self.assertEqual(_sentence_adr_cases(), SENTENCE_COUNT_CASES)

    def test_prose(self):
        text = (
            "Dr. Brown arrived at 3 p.m. today. Did he bring the files, e.g. the 2.5 MB "
            "report? He did! Then... nothing happened."
        )
        self.assertEqual(sentence_count(text), 4)

    def test_closing_bracket_after_terminator(self):
        self.assertEqual(sentence_count("It worked (mostly.) Next one."), 2)

    def test_non_str_raises_type_error(self):
        for value in (None, 42, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    sentence_count(value)


    def test_long_terminator_runs_are_linear(self):
        # Regression: before the run in _SENTENCE_END was anchored to be maximal, these took
        # seconds (quadratic backtracking: 2.9 s at 8000 characters). They now take
        # milliseconds; the 1 s bound leaves a wide margin on a loaded machine.
        for text in ("." * 20000 + "x", "a.. " + "!" * 20000 + "x"):
            with self.subTest(text=text[:6]):
                start = time.perf_counter()
                sentence_count(text)
                self.assertLess(time.perf_counter() - start, 1.0)

if __name__ == "__main__":
    unittest.main()
