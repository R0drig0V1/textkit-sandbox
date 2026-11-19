"""Tests for textkit.counts. One TestCase class per public function."""

import ast
import pathlib
import re
import unittest
import unittest.mock

from textkit.counts import char_freq, word_count
from textkit.counts import reading_time

# The table of cases at the end of the word-rule ADR, row by row (input, count). Kept as
# code so the cases are readable here; `test_cases_match_the_adr_table` keeps both in sync.
WORD_COUNT_CASES = [
    ("", 0),
    ("hello", 1),
    ("Hello, world!", 2),
    ("  one   two \n\n three\t", 3),
    ("!!! ... ---", 0),
    ("well-known", 1),
    ("state-of-the-art design", 2),
    ("a - b", 2),
    ("a--b", 2),
    ("-5", 1),
    ("1-2", 1),
    ("don't", 1),
    ("don’t", 1),
    ("rock'n'roll", 1),
    ("'quoted' students'", 2),
    ("e-mail's", 1),
    ("42", 1),
    ("3.14 and 1,000,000", 3),
    ("v2.0", 1),
    ("U.S.A.", 3),
    ("end. Next", 2),
    ("x2 3x", 2),
    ("C++", 1),
    ("snake_case", 2),
    ("well—maybe", 2),
    ("naïve café", 2),
    ("naïve", 1),
    ("́", 0),
    ("日本語", 1),
    ("\U0001f642", 0),
]


def _adr_cases() -> list[tuple[str, int]]:
    """Parse the case table of the word-rule ADR (found by slug, so renumbering is safe)."""
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-what-counts-as-a-word.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(ast.literal_eval(literal), int(count)) for literal, count in rows]


class WordCountTest(unittest.TestCase):
    def test_every_case_of_the_adr_table(self):
        for text, expected in WORD_COUNT_CASES:
            with self.subTest(text=text):
                self.assertEqual(word_count(text), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(_adr_cases(), WORD_COUNT_CASES)

    def test_rejects_non_str(self):
        for value in (None, b"two words", ["a", "b"], 3):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    word_count(value)  # type: ignore[arg-type]



class CharFreqTest(unittest.TestCase):
    def test_counts_each_character(self):
        self.assertEqual(char_freq("banana"), {"b": 1, "a": 3, "n": 2})

    def test_empty_text(self):
        self.assertEqual(char_freq(""), {})

    def test_whitespace_is_not_counted(self):
        self.assertEqual(char_freq("a b\tc\nd\r\n"), {"a": 1, "b": 1, "c": 1, "d": 1})

    def test_unicode_whitespace_is_not_counted(self):
        # No-break space, em space, line separator, vertical tab, form feed.
        self.assertEqual(char_freq("\u00a0\u2003\u2028\x0b\x0c"), {})
        self.assertEqual(char_freq("x\u00a0x"), {"x": 2})

    def test_is_case_sensitive(self):
        self.assertEqual(char_freq("aAa"), {"a": 2, "A": 1})

    def test_keys_in_order_of_first_occurrence(self):
        self.assertEqual(list(char_freq("hello, world")), ["h", "e", "l", "o", ",", "w", "r", "d"])

    def test_punctuation_digits_and_symbols_are_counted(self):
        self.assertEqual(char_freq("1+1=2!"), {"1": 2, "+": 1, "=": 1, "2": 1, "!": 1})

    def test_counts_code_points_without_normalization(self):
        self.assertEqual(char_freq("e\u0301\u00e9"), {"e": 1, "\u0301": 1, "\u00e9": 1})
        self.assertEqual(char_freq("\U0001f642\U0001f642"), {"\U0001f642": 2})

    def test_returns_a_plain_dict(self):
        self.assertIs(type(char_freq("ab")), dict)

    def test_rejects_non_str(self):
        for value in (None, b"ab", ["a", "b"], 3):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    char_freq(value)  # type: ignore[arg-type]


# The table of cases at the end of the reading-time ADR, row by row (text, wpm, minutes).
# Long inputs are written as in the ADR, a literal repeated with `*`.
READING_TIME_CASES = [
    ("", 200, 0),
    ("  \n\t ", 200, 0),
    ("!!! ... \U0001f642", 200, 0),
    ("hello", 200, 1),
    ("word " * 199, 200, 1),
    ("word " * 200, 200, 1),
    ("word " * 201, 200, 2),
    ("word " * 400, 200, 2),
    ("word " * 1000, 250, 4),
    ("one two three", 1, 3),
    ("one two three", 2, 2),
    ("well-known don't 3.14", 1, 3),
    ("hello", 1000000, 1),
]


def _adr_text(expression: str) -> str:
    """Evaluate an ADR input: a string literal, or a string literal times an int literal."""
    node = ast.parse(expression, mode="eval").body
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return ast.literal_eval(node.left) * ast.literal_eval(node.right)
    return ast.literal_eval(node)


def _reading_time_adr_cases() -> list[tuple[str, int, int]]:
    """Parse the case table of the reading-time ADR (found by slug, so renumbering is safe)."""
    root = pathlib.Path(__file__).resolve().parent.parent
    (adr,) = (root / "docs" / "decisions").glob("*-reading-time-rounds-up.md")
    rows = re.findall(r"^\| `(.*)` \| (\d+) \| (\d+) \|", adr.read_text(encoding="utf-8"), re.M)
    return [(_adr_text(expr), int(wpm), int(minutes)) for expr, wpm, minutes in rows]


class ReadingTimeTest(unittest.TestCase):
    def test_every_case_of_the_adr_table(self):
        for text, wpm, expected in READING_TIME_CASES:
            with self.subTest(text=text[:30], wpm=wpm):
                self.assertEqual(reading_time(text, wpm=wpm), expected)

    def test_cases_match_the_adr_table(self):
        self.assertEqual(_reading_time_adr_cases(), READING_TIME_CASES)

    def test_default_wpm_is_200(self):
        text = "word " * 201
        self.assertEqual(reading_time(text), reading_time(text, 200))
        self.assertEqual(reading_time(text), 2)
        self.assertEqual(reading_time("word " * 250), 2)

    def test_counts_words_with_word_count(self):
        # reading_time must not split words itself, so a change to the word rule reaches it.
        with unittest.mock.patch("textkit.counts.word_count", return_value=401) as count:
            self.assertEqual(reading_time("anything", 200), 3)
        count.assert_called_once_with("anything")

    def test_is_exact_for_very_large_counts(self):
        with unittest.mock.patch("textkit.counts.word_count", return_value=10**20 + 1):
            self.assertEqual(reading_time("x", 10**20), 2)

    def test_wpm_below_one_raises_value_error(self):
        for wpm in (0, -1, -200):
            with self.subTest(wpm=wpm):
                with self.assertRaises(ValueError):
                    reading_time("hello", wpm)

    def test_wpm_below_one_raises_even_for_empty_text(self):
        with self.assertRaises(ValueError):
            reading_time("", 0)

    def test_rejects_non_int_wpm(self):
        for wpm in (200.0, 1.5, "200", None, True):
            with self.subTest(wpm=wpm):
                with self.assertRaises(TypeError):
                    reading_time("hello", wpm)  # type: ignore[arg-type]

    def test_rejects_non_str_text(self):
        for value in (None, b"two words", ["a", "b"], 3):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    reading_time(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
