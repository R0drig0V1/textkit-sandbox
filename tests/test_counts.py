"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest

from textkit.counts import char_freq, reading_time, sentence_count, word_count

# Every row of the case table in ADR 0002 (what counts as a word), in the same order.
WORD_COUNT_CASES = [
    ("", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("a--b", 2),
    ("-dash- start", 2),
    ("a—b", 2),
    ("42", 1),
    ("3.14", 1),
    ("1,000,000", 1),
    ("-5", 1),
    ("$5 or 5%", 3),
    ("Chapter 1.", 2),
    ("1, 2, 3", 3),
    ("v1.2", 1),
    ("hello123", 1),
    ("don't", 1),
    ("don’t", 1),
    ("rock'n'roll", 1),
    ("the students' books", 3),
    ("'quoted'", 1),
    ("e.g.", 2),
    ("example.com", 2),
    ("snake_case", 2),
    ("camelCase", 1),
    ("naïve café", 2),
    ("Ñandú", 1),
    ("́", 0),
    ("日本語", 1),
    ("!!! ... ?", 0),
    (" \n\t ", 0),
    ("  a \n\n b\t c  ", 3),
]


def _adr_cases() -> list:
    """Parse the case table of the word ADR (found by title, so renumbering does not break it)."""
    root = pathlib.Path(__file__).resolve().parents[1]
    (adr,) = (root / "docs" / "decisions").glob("*-what-counts-as-a-word.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(text), int(count)) for text, count in rows]


class WordCountTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_adr_table(self):
        # Keeps "tests every row" true when the ADR table changes.
        self.assertEqual(WORD_COUNT_CASES, _adr_cases())

    def test_nfc_and_nfd_agree(self):
        self.assertEqual(word_count("Ñandú"), word_count("Ñandú"))

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            word_count(["a", "b"])  # type: ignore[arg-type]


class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("cabbage")), ["c", "a", "b", "g", "e"])

    def test_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_whitespace_not_counted(self):
        # Space, tab, newline, carriage return, no-break space, em space, line separator.
        self.assertEqual(char_freq(" a\tb\nc\r\u00a0\u2003\u2028a "), {"a": 2, "b": 1, "c": 1})

    def test_punctuation_and_digits_counted(self):
        self.assertEqual(char_freq("a, 1!1"), {"a": 1, ",": 1, "1": 2, "!": 1})

    def test_empty_and_whitespace_only(self):
        self.assertEqual(char_freq(""), {})
        self.assertEqual(char_freq(" \n\t "), {})

    def test_no_normalization(self):
        self.assertEqual(char_freq("\u00fa"), {"\u00fa": 1})
        self.assertEqual(char_freq("u\u0301"), {"u": 1, "\u0301": 1})

    def test_returns_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            char_freq(["a", "b"])  # type: ignore[arg-type]


class ReadingTimeTest(unittest.TestCase):
    def test_no_words_is_zero(self):
        self.assertEqual(reading_time(""), 0)
        self.assertEqual(reading_time(" \n\t "), 0)
        self.assertEqual(reading_time("!!! ... ?"), 0)

    def test_under_one_minute_rounds_up_to_one(self):
        self.assertEqual(reading_time("hello"), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 199)), 1)

    def test_rounds_up_at_the_boundary(self):
        self.assertEqual(reading_time(" ".join(["w"] * 200)), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 201)), 2)
        self.assertEqual(reading_time(" ".join(["w"] * 400)), 2)
        self.assertEqual(reading_time(" ".join(["w"] * 401)), 3)

    def test_custom_wpm(self):
        self.assertEqual(reading_time("a b c", wpm=1), 3)
        self.assertEqual(reading_time("a b c", wpm=2), 2)
        self.assertEqual(reading_time("a b c", wpm=3), 1)
        self.assertEqual(reading_time(" ".join(["w"] * 500), wpm=250), 2)

    def test_uses_word_count(self):
        # "well-known" is one word and "e.g." two (ADR 0002), so 3 words at 3 wpm is 1 minute.
        self.assertEqual(reading_time("well-known e.g.", wpm=3), 1)
        self.assertEqual(reading_time("well-known e.g.", wpm=2), 2)

    def test_wpm_below_one_raises_value_error(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm), self.assertRaises(ValueError):
                reading_time("hello", wpm=wpm)

    def test_wpm_below_one_raises_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            reading_time("", wpm=0)

    def test_rejects_non_int_wpm(self):
        for wpm in (200.0, "200", None, True):
            with self.subTest(wpm=wpm), self.assertRaises(TypeError):
                reading_time("hello", wpm=wpm)  # type: ignore[arg-type]

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            reading_time(["a", "b"])  # type: ignore[arg-type]


def _sentence_adr_cases() -> list:
    """Parse the case table of the sentence ADR (found by title, so renumbering does not break it)."""
    root = pathlib.Path(__file__).resolve().parents[1]
    (adr,) = (root / "docs" / "decisions").glob("*-what-ends-a-sentence.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|$", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(text), int(count)) for text, count in rows]


# Every row of the case table in ADR 0005 (what ends a sentence), in the same order.
SENTENCE_COUNT_CASES = [
    ("", 0),
    ("Hello", 1),
    ("Hello.", 1),
    ("Hello. World.", 2),
    ("Hello! World? Yes.", 3),
    ("Really?!", 1),
    ("Stop!!! Now.", 2),
    ("One. Two", 2),
    ("3.14 is pi.", 1),
    ("Visit example.com today.", 1),
    ("Hello.World", 1),
    ("Version 2. Then 3.", 2),
    ("Use a tool, e.g. a hammer.", 1),
    ("Use a tool, e.g. Python.", 1),
    ("Use i.e., this one.", 1),
    ("I met Dr. Smith. He was kind.", 2),
    ("Mr. and Mrs. Smith left.", 1),
    ("Apples, pears, etc. and more.", 1),
    ("Apples, pears, etc. Then we left.", 2),
    ("Wait... what?", 1),
    ("Wait... What?", 2),
    ("Wait… What?", 2),
    ("Wait...what?", 1),
    ("...and then.", 1),
    ("Hmm...", 1),
    ('He said "Hi." Then he left.', 2),
    ('"Help!" she cried.', 1),
    ("(It works.) Good.", 2),
    ("¿Qué tal? Bien.", 2),
    ("Ñandú. Ñandú.", 2),
    ("Line one.\nLine two.", 2),
    ("Title\n\nBody text.", 1),
    ("Ask the Dr. Then go.", 1),
    ("J. R. R. Tolkien wrote it.", 4),
    ("U.S. Army", 2),
    ("Is it? yes.", 1),
    ("你好。再见。", 1),
    ("!!! ... ?", 0),
    (" \n\t ", 0),
]


class SentenceCountTest(unittest.TestCase):
    def test_adr_table(self):
        for text, expected in SENTENCE_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(sentence_count(text), expected)

    def test_cases_match_adr_table(self):
        # Keeps "tests every row" true when the ADR table changes.
        self.assertEqual(SENTENCE_COUNT_CASES, _sentence_adr_cases())

    def test_abbreviations_ignore_case(self):
        self.assertEqual(sentence_count("DR. Smith is here."), 1)
        self.assertEqual(sentence_count("E.g. Python is one."), 1)

    def test_abbreviation_needs_a_single_dot(self):
        # Only a lone "." after an abbreviation is exempt; "Dr..." is an ellipsis.
        self.assertEqual(sentence_count("Ask the Dr... Then go."), 2)

    def test_nfc_and_nfd_agree(self):
        nfd = "N\u0303andu\u0301. N\u0303andu\u0301."  # decomposed "Ñandú. Ñandú."
        self.assertEqual(sentence_count(nfd), sentence_count("Ñandú. Ñandú."))

    def test_long_punctuation_runs(self):
        # Many terminator runs before a lower-case word: one sentence, in linear time.
        self.assertEqual(sentence_count("a" + " ." * 100_000 + " b"), 1)

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            sentence_count(b"Hello.")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
