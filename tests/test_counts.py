"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, ngrams, reading_time, sentence_count, word_count

# The case table of the word-rule ADR (docs/decisions/*-word-count-what-counts-as-a-word.md),
# row by row. Kept literal here so a failure names the input; WordCountTest also checks that
# the ADR table lists exactly these rows.
WORD_COUNT_CASES = [
    ("", 0),
    ("   \n\t  ", 0),
    ("!!! ... ---", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("well-known", 1),
    ("R2-D2", 1),
    ("rock--roll", 2),
    ("a - b", 2),
    ("don't", 1),
    ("don’t", 1),
    ("'quoted' dogs'", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("end.Start", 2),
    ("a  b\n\nc\td", 4),
    ("snake_case", 2),
    ("naïve café", 2),
    ("año 2026", 2),
    ("nai\u0308ve cafe\u0301", 2),  # NFD of "naïve café"
    ("N\u0303andu\u0301", 1),  # NFD of "Ñandú"
    ("\u0939\u093f\u0928\u094d\u0926\u0940", 1),  # Hindi, vowel signs are Mc/Mn marks
    ("\u0301 a", 1),  # a mark with no letter before it is not a word
]


def _adr_cases() -> list:
    """Parse the ADR case table into (input, count) pairs.

    The ADR is found by its slug, not its number, because the integrator may renumber it.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-word-count-what-counts-as-a-word.md")
    text = adr.read_text(encoding="utf-8")
    table = text.split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(src), int(n)) for src, n in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    word_count(bad)


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("hello"), {"h": 1, "e": 1, "l": 2, "o": 1})

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_skips_every_isspace_character(self):
        # space, tab, newline, carriage return, vertical tab, form feed, NBSP, em space,
        # line separator, ideographic space: all have str.isspace() true.
        spaces = " \t\n\r\v\f\u00a0\u2003\u2028\u3000"
        self.assertTrue(all(ch.isspace() for ch in spaces))
        self.assertEqual(char_freq(f"a{spaces}b"), {"a": 1, "b": 1})

    def test_keys_in_order_of_first_occurrence(self):
        result = char_freq("banana split")
        self.assertEqual(list(result), ["b", "a", "n", "s", "p", "l", "i", "t"])
        self.assertEqual(result["a"], 3)
        self.assertEqual(result["n"], 2)

    def test_punctuation_and_digits_are_counted(self):
        self.assertEqual(char_freq("a1!a1!"), {"a": 2, "1": 2, "!": 2})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq("  \n\t "), {})

    def test_code_points_without_normalization(self):
        # NFD "é" is "e" plus a combining acute accent: two code points, two keys.
        self.assertEqual(char_freq("e\u0301"), {"e": 1, "\u0301": 1})
        self.assertEqual(char_freq("\u00e9"), {"\u00e9": 1})

    def test_returns_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3, ["a"]):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    char_freq(bad)


# The case table of the rounding ADR (docs/decisions/*-reading-time-rounding.md), row by row.
# Each row is (text, wpm, minutes); ReadingTimeTest also checks the ADR lists exactly these.
READING_TIME_CASES = [
    ("", 200, 0),
    ("   \n\t  ", 200, 0),
    ("!!! ... ---", 200, 0),
    ("hello", 200, 1),
    (" ".join(["word"] * 199), 200, 1),
    (" ".join(["word"] * 200), 200, 1),
    (" ".join(["word"] * 201), 200, 2),
    (" ".join(["word"] * 400), 200, 2),
    (" ".join(["word"] * 401), 200, 3),
    ("well-known don't 3.14", 3, 1),
    ("well-known don't 3.14", 2, 2),
    ("a b c", 1, 3),
]


def _reading_time_adr_cases() -> list:
    """Parse the rounding ADR's case table into (text, wpm, minutes) triples.

    Found by slug, not number, because the integrator may renumber it. The input column is a
    Python expression (string literals, ``" ".join(...)``), evaluated with no builtins.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-reading-time-rounding.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \| (\d+) \|$", table, re.M)
    return [(eval(src, {"__builtins__": {}}), int(w), int(m)) for src, w, m in rows]


class ReadingTimeTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, wpm, expected in READING_TIME_CASES:
            with self.subTest(text=text[:30], wpm=wpm):
                self.assertEqual(reading_time(text, wpm), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_reading_time_adr_cases(), READING_TIME_CASES)

    def test_default_wpm_is_200(self):
        self.assertEqual(reading_time(" ".join(["w"] * 200)), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 201)), 2)

    def test_counts_words_with_word_count(self):
        # Punctuation is not a word (ADR 0002), so it does not add reading time.
        text = "one, two -- three!!! " * 100
        self.assertEqual(word_count(text), 300)
        self.assertEqual(reading_time(text, 100), 3)

    def test_wpm_below_one_raises_value_error(self):
        for bad in (0, -1, -200):
            with self.subTest(wpm=bad):
                with self.assertRaises(ValueError):
                    reading_time("hello", bad)
        # Checked before the text is read: empty text does not short-circuit to 0.
        with self.assertRaises(ValueError):
            reading_time("", 0)

    def test_non_int_wpm_raises_type_error(self):
        for bad in (200.0, "200", None, True):
            with self.subTest(wpm=bad):
                with self.assertRaises(TypeError):
                    reading_time("hello", bad)

    def test_rejects_non_str(self):
        for bad in (b"hello", None, 3):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    reading_time(bad)


# The case table of the sentence-rule ADR
# (docs/decisions/*-sentence-count-abbreviations-and-ellipses.md), row by row, kept literal
# like WORD_COUNT_CASES; SentenceCountTest checks the ADR table lists exactly these rows.
SENTENCE_COUNT_CASES = [
    ("", 0),
    ("   \n\t ", 0),
    ("...", 0),
    ("!?! …", 0),
    ("Hello", 1),
    ("Hello.", 1),
    ("Hello. World.", 2),
    ("Is it? Yes! Good.", 3),
    ("Really?! Yes.", 2),
    ("Pi is 3.14. It is irrational.", 2),
    ("Visit example.com today.", 1),
    ("Version 1.2.3 is out. Get it.", 2),
    ("Dr. Smith arrived. He sat.", 2),
    ("Ask MR. Jones or mrs. Lee.", 1),
    ("Some cities, e.g. Paris, are big.", 1),
    ("Kramer vs. Kramer won. It is old.", 2),
    ("(Prof. Lee) Hi.", 1),
    ("J. R. R. Tolkien wrote it.", 1),
    ("We bought pens, etc. Then we left.", 2),  # "etc." is not in the list
    ("We bought pens, etc. and paper.", 1),  # ...but lower case continues the sentence
    ("I met John Smith Jr. He waved.", 2),
    ("I saw the Dr. Then I left.", 1),  # known wrong answer: titles precede a name
    ("Wait... What?", 2),
    ("Wait… What?", 2),
    ("He paused... then left.", 1),
    ("And so...", 1),
    ("Hello. ... World.", 2),
    ("\"Wow!\" he said.", 1),
    ("He said \"Stop.\" Then he left.", 2),
    ("(It works.) Next one.", 2),
    ("first. second.", 1),  # known wrong answer: lower-case sentence starts
    ("Title\n\nBody text", 1),
    ("Ça va? Oui.", 2),
    ("日本語。英語。", 1),  # "。" is not a terminator
]


def _sentence_adr_cases() -> list:
    """Parse the sentence-rule ADR case table into (input, count) pairs, found by slug."""
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-sentence-count-abbreviations-and-ellipses.md")
    table = adr.read_text(encoding="utf-8").split("## Cases", 1)[1]
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", table, re.M)
    return [(ast.literal_eval(src), int(n)) for src, n in rows]


class SentenceCountTest(unittest.TestCase):
    def test_adr_cases(self):
        for text, expected in SENTENCE_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(sentence_count(text), expected)

    def test_cases_match_adr_table(self):
        self.assertEqual(_sentence_adr_cases(), SENTENCE_COUNT_CASES)

    def test_every_listed_abbreviation(self):
        for abbr in ("Dr.", "Mr.", "Mrs.", "Ms.", "Mx.", "Prof.", "vs.", "e.g.", "i.e."):
            with self.subTest(abbr=abbr):
                self.assertEqual(sentence_count(f"See {abbr} Lee now. Done."), 2)
                self.assertEqual(sentence_count(f"See {abbr.upper()} Lee now. Done."), 2)

    def test_abbreviation_only_before_a_single_dot(self):
        # "Dr.." or "Dr.!" is not the abbreviation's own dot, so it is an ordinary end.
        self.assertEqual(sentence_count("Ask the Dr.. Then go."), 2)
        self.assertEqual(sentence_count("Ask the Dr! Then go."), 2)

    def test_closers_after_terminator(self):
        for text in ("He said \u201cGo.\u201d Then left.", "A (bee.) C.", "\u00abNon.\u00bb Oui."):
            with self.subTest(text=text):
                self.assertEqual(sentence_count(text), 2)

    def test_mark_without_letter_is_not_a_sentence(self):
        # ADR 0002: a combining mark with no letter before it is not a word.
        self.assertEqual(sentence_count("Hi. \u0301. Bye."), 2)

    def test_matches_word_count_zero(self):
        for text in ("", "?!", "- -- ...", "\u0301"):
            with self.subTest(text=text):
                self.assertEqual(word_count(text), 0)
                self.assertEqual(sentence_count(text), 0)

    def test_rejects_non_str(self):
        for bad in (b"Hello.", None, 3, ["Hello."]):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    sentence_count(bad)


class NgramsTest(unittest.TestCase):
    def test_default_is_bigrams(self):
        self.assertEqual(
            ngrams("the quick brown fox"),
            [("the", "quick"), ("quick", "brown"), ("brown", "fox")],
        )

    def test_trigrams(self):
        self.assertEqual(
            ngrams("a b c d", 3),
            [("a", "b", "c"), ("b", "c", "d")],
        )

    def test_unigrams(self):
        self.assertEqual(ngrams("one two", 1), [("one",), ("two",)])

    def test_n_equal_to_word_count_gives_one_tuple(self):
        self.assertEqual(ngrams("a b c", 3), [("a", "b", "c")])

    def test_fewer_than_n_words_gives_empty_list(self):
        for text, n in (("", 1), ("", 2), ("   ", 1), ("!!! ...", 1), ("one", 2), ("a b", 3)):
            with self.subTest(text=text, n=n):
                self.assertEqual(ngrams(text, n), [])

    def test_count_is_words_minus_n_plus_one(self):
        text = "Hello, world! It's a well-known fact: 3.14 is pi."
        for n in range(1, 12):
            with self.subTest(n=n):
                self.assertEqual(len(ngrams(text, n)), max(word_count(text) - n + 1, 0))

    def test_words_follow_adr_0002(self):
        # Hyphens, apostrophes and digit separators join; punctuation and "_" do not.
        self.assertEqual(
            ngrams("well-known don't 3.14 snake_case"),
            [("well-known", "don't"), ("don't", "3.14"), ("3.14", "snake"), ("snake", "case")],
        )

    def test_words_exactly_as_in_text(self):
        # No case-folding and no normalization: the NFD word keeps its combining mark.
        self.assertEqual(
            ngrams("Hello HELLO cafe\u0301", 2),
            [("Hello", "HELLO"), ("HELLO", "cafe\u0301")],
        )

    def test_punctuation_and_newlines_do_not_stop_a_run(self):
        self.assertEqual(ngrams("End.\nStart, again"), [("End", "Start"), ("Start", "again")])

    def test_repeated_runs_appear_once_per_occurrence(self):
        self.assertEqual(ngrams("a b a b"), [("a", "b"), ("b", "a"), ("a", "b")])

    def test_returns_list_of_tuples(self):
        result = ngrams("a b c")
        self.assertIs(type(result), list)
        for gram in result:
            self.assertIs(type(gram), tuple)

    def test_n_below_one_raises_value_error(self):
        for bad in (0, -1, -5):
            with self.subTest(n=bad):
                with self.assertRaises(ValueError):
                    ngrams("a b c", bad)
        # Checked before the text is read: empty text does not short-circuit to [].
        with self.assertRaises(ValueError):
            ngrams("", 0)

    def test_non_int_n_raises_type_error(self):
        for bad in (2.0, "2", None, True):
            with self.subTest(n=bad):
                with self.assertRaises(TypeError):
                    ngrams("a b c", bad)

    def test_rejects_non_str(self):
        for bad in (b"a b", None, 3, ["a", "b"]):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    ngrams(bad)


if __name__ == "__main__":
    unittest.main()
