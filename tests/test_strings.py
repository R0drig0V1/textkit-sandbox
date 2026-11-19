"""Tests for textkit.strings: one TestCase class per public function.

`WrapTest` checks every row of the case table that ends ADR 0003
(docs/decisions/0003-wrap-newlines.md), read from the ADR itself so the table and the code
cannot drift apart.
"""

import ast
import pathlib
import re
import unicodedata
import unittest

from textkit.strings import slugify, squeeze, strip_accents, truncate, wrap

_WRAP_ADR = (
    pathlib.Path(__file__).resolve().parents[1] / "docs" / "decisions" / "0003-wrap-newlines.md"
)
# A table row: | `input literal` | width | `output literal` | description |
_WRAP_ROW = re.compile(r"^\| `(?P<input>[^`]*)` \| (?P<width>\d+) \| `(?P<output>[^`]*)` \| .+ \|$")


def _wrap_adr_cases() -> list[tuple[str, int, list[str]]]:
    """Return (input, width, output) for every row of ADR 0003's "Cases" table."""
    section = _WRAP_ADR.read_text(encoding="utf-8").split("\n## Cases\n", 1)[1]
    return [
        (ast.literal_eval(m["input"]), int(m["width"]), ast.literal_eval(m["output"]))
        for m in map(_WRAP_ROW.match, section.splitlines())
        if m
    ]


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_joins_words(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_non_ascii_removed_without_separator(self):
        self.assertEqual(slugify("naïve"), "nave")

    def test_nfc_input_drops_precomposed_letters(self):
        self.assertEqual(slugify("Ñandú"), "and")  # "Ñandú", NFC as typed

    def test_nfd_input_keeps_base_letters(self):
        self.assertEqual(slugify("Ñandú"), "nandu")  # "Ñandú", NFD

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_separators(self):
        self.assertEqual(slugify("!!!"), "")

    def test_underscore_is_a_separator(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_run_of_mixed_separators_becomes_one_dash(self):
        self.assertEqual(slugify("a  _-!? b"), "a-b")

    def test_strips_dashes_at_both_ends(self):
        self.assertEqual(slugify("--Hello--"), "hello")

    def test_digits_kept(self):
        self.assertEqual(slugify("Python 3.9"), "python-3-9")

    def test_non_ascii_removed_before_lowercasing(self):
        # U+212A KELVIN SIGN lower-cases to ASCII "k"; it must be removed, not kept.
        self.assertEqual(slugify("5K run"), "5-run")


class StripAccentsTest(unittest.TestCase):
    def test_plan_example(self):
        self.assertEqual(strip_accents("Ñandú"), "Nandu")

    def test_nfd_input_gives_same_result(self):
        self.assertEqual(strip_accents(unicodedata.normalize("NFD", "Ñandú")), "Nandu")

    def test_several_marks(self):
        self.assertEqual(strip_accents("crème brûlée, naïve, Ångström"),
                         "creme brulee, naive, Angstrom")

    def test_stacked_marks_on_one_letter(self):
        # "ệ" carries two marks (circumflex and dot below).
        self.assertEqual(strip_accents("Việt"), "Viet")

    def test_letters_without_combining_marks_are_kept(self):
        self.assertEqual(strip_accents("ø ł ß"), "ø ł ß")

    def test_plain_and_empty_text_unchanged(self):
        self.assertEqual(strip_accents("plain ASCII 123"), "plain ASCII 123")
        self.assertEqual(strip_accents(""), "")

    def test_lone_combining_mark_removed(self):
        self.assertEqual(strip_accents("a\u0301\u0301"), "a")

    def test_non_mark_decompositions_are_recomposed(self):
        self.assertEqual(strip_accents("한국어"), "한국어")

    def test_non_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            strip_accents(None)  # type: ignore[arg-type]


class TruncateTest(unittest.TestCase):
    def test_text_that_fits_is_unchanged(self):
        self.assertEqual(truncate("Hello", 10), "Hello")

    def test_text_exactly_width_is_unchanged(self):
        self.assertEqual(truncate("Hello", 5), "Hello")

    def test_long_text_is_cut_to_exactly_width_with_suffix(self):
        result = truncate("Hello, World!", 8)
        self.assertEqual(result, "Hello...")
        self.assertEqual(len(result), 8)

    def test_cut_keeps_the_start_of_text(self):
        self.assertEqual(truncate("abcdefghij", 6), "abc...")

    def test_custom_suffix(self):
        self.assertEqual(truncate("Hello, World!", 7, suffix="~"), "Hello,~")

    def test_empty_suffix_is_a_plain_cut(self):
        self.assertEqual(truncate("Hello, World!", 5, suffix=""), "Hello")

    def test_width_equal_to_suffix_length_gives_only_suffix(self):
        self.assertEqual(truncate("Hello, World!", 3), "...")

    def test_width_zero_with_empty_suffix(self):
        self.assertEqual(truncate("x", 0, suffix=""), "")
        self.assertEqual(truncate("", 0, suffix=""), "")

    def test_width_smaller_than_suffix_raises(self):
        with self.assertRaises(ValueError):
            truncate("Hello, World!", 2)

    def test_width_smaller_than_suffix_raises_even_if_text_fits(self):
        with self.assertRaises(ValueError):
            truncate("Hi", 2)
        with self.assertRaises(ValueError):
            truncate("", 0)

    def test_negative_width_raises(self):
        with self.assertRaises(ValueError):
            truncate("Hello", -1, suffix="")

    def test_length_counts_code_points(self):
        self.assertEqual(truncate("Ñandú", 5), "Ñandú")
        self.assertEqual(truncate("Ñandú!", 5), "Ña...")


class WrapTest(unittest.TestCase):
    def test_adr_table_is_present(self):
        # A parsing slip must not silently empty the table.
        inputs = [case[0] for case in _wrap_adr_cases()]
        self.assertGreaterEqual(len(inputs), 19)
        for required in ["", "a\nb", "a\n\nb", "a\r\nb", "a\u00a0b c", "abcdefghij xy"]:
            self.assertIn(required, inputs)

    def test_every_adr_row(self):
        for text, width, output in _wrap_adr_cases():
            with self.subTest(text=text, width=width):
                self.assertEqual(wrap(text, width), output)

    def test_lines_fit_and_never_hold_the_separating_space(self):
        text = "  Lorem ipsum dolor\tsit amet,\n\nconsectetur   adipiscing elit sed do  "
        for width in range(1, 30):
            with self.subTest(width=width):
                lines = wrap(text, width)
                self.assertEqual(" ".join(lines), " ".join(text.split()))
                for line in lines:
                    self.assertTrue(line)
                    self.assertEqual(line, line.strip())
                    self.assertNotIn("  ", line)
                    self.assertTrue(len(line) <= width or " " not in line)

    def test_width_below_one_raises(self):
        for text in ["", "a b"]:
            for width in [0, -1]:
                with self.subTest(text=text, width=width):
                    with self.assertRaises(ValueError):
                        wrap(text, width)

    def test_rejects_non_str_text(self):
        for value in [None, b"two words", ["a", "b"]]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    wrap(value, 5)

    def test_rejects_non_int_width(self):
        for width in [None, 2.5, "5"]:
            with self.subTest(width=width):
                with self.assertRaises(TypeError):
                    wrap("a b", width)


if __name__ == "__main__":
    unittest.main()
