"""Tests for textkit._tokens (plan task T1.10, the shared tokenizer).

`WordsTest` asserts `words` on every row of the case table in ADR 0001
(docs/decisions/0001-word-rule.md), one assertion per row, and checks that CASES below and
that table stay identical, so neither can change without the other. It also pins where
`words` agrees with ADR 0002 (docs/decisions/0002-splitting-runs-of-capitals.md), which is
the part of `to_snake_case` that goes through it.
"""

import ast
import pathlib
import re
import unittest

from textkit._tokens import words

_DECISIONS = pathlib.Path(__file__).resolve().parents[1] / "docs" / "decisions"
# A row of ADR 0001's table: | `input literal` | count | `words literal` | description |
_ROW = re.compile(r"^\| `(?P<input>[^`]*)` \| (?P<count>\d+) \| `(?P<words>[^`]*)` \| .+ \|$")

# (input, words), in the order of the ADR 0001 table. Invisible or non-ASCII characters are
# written as escapes so that a reader can tell the NFC and NFD rows apart.
CASES = [
    ("", []),
    ("   ", []),
    ("\n\n", []),
    ("a  b\n\nc\td", ["a", "b", "c", "d"]),
    ("Hello, world!", ["Hello", "world"]),
    ("...", []),
    ("!?, -- ;", []),
    ("well-known", ["well-known"]),
    ("state-of-the-art", ["state-of-the-art"]),
    ("well--known", ["well", "known"]),
    ("- dash -", ["dash"]),
    ("don't", ["don't"]),
    ("don’t", ["don’t"]),
    ("rock'n'roll", ["rock'n'roll"]),
    ("students' books", ["students", "books"]),
    ("'quoted'", ["quoted"]),
    ("42", ["42"]),
    ("3.14", ["3.14"]),
    ("1,000,000", ["1,000,000"]),
    ("v1.2.3", ["v1.2.3"]),
    ("-5 degrees", ["5", "degrees"]),
    ("50% off", ["50", "off"]),
    ("1.5.", ["1.5"]),
    ("e.g.", ["e", "g"]),
    ("end.Start", ["end", "Start"]),
    ("foo_bar", ["foo", "bar"]),
    ("camelCase", ["camelCase"]),
    ("C++ and C#", ["C", "and", "C"]),
    ("café", ["café"]),
    ("café", ["café"]),
    ("́abc", ["abc"]),
    ("Привет, мир",
     ["Привет", "мир"]),
    ("日本語", ["日本語"]),
    ("\U0001f642 ok", ["ok"]),
]

# Inputs of ADR 0002's table made only of letters, digits and "_": `to_snake_case` splits
# them at "_" with `words`. The other rows ("kebab-case", "mixed-kebab_snakeCase", "a--b__c",
# "---") contain "-", where the two ADRs disagree, so they keep the ADR 0002 splitter.
_ADR_0002_PLAIN = [
    "HTTPServer", "parseURL2", "camelCase", "PascalCase", "already_snake", "",
    "getHTTPResponseCode", "IOError", "ABC", "ABCd", "URL2Path", "utf8Decode", "v2beta",
    "SCREAMING_SNAKE", "__init__", "aB", "A", "ÉtéCase",
]


def _adr_0001_table() -> list[tuple[str, list[str]]]:
    """Return the (input, words) rows of the "Cases" table in ADR 0001."""
    text = (_DECISIONS / "0001-word-rule.md").read_text(encoding="utf-8")
    section = text.split("\n## Cases\n", 1)[1]
    return [
        (ast.literal_eval(m["input"]), ast.literal_eval(m["words"]))
        for m in map(_ROW.match, section.splitlines())
        if m
    ]


def _adr_0002_inputs() -> list[str]:
    """Return the inputs of the case table in ADR 0002, in order."""
    text = (_DECISIONS / "0002-splitting-runs-of-capitals.md").read_text(encoding="utf-8")
    return [ast.literal_eval(a) for a in re.findall(r"^\| `(\".*?\")` \| `", text, re.M)]


class WordsTest(unittest.TestCase):
    def test_every_row_of_adr_0001(self):
        for text, expected in CASES:
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_adr_0001_table_matches_cases(self):
        self.assertEqual(_adr_0001_table(), CASES)

    def test_rejects_non_str(self):
        for value in [None, b"two words", ["a", "b"], 3]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    words(value)  # type: ignore[arg-type]

    def test_plain_rows_of_adr_0002_are_exactly_those_without_other_characters(self):
        # Keeps the list above (and the PR's list of rows) in step with ADR 0002's table.
        plain = [n for n in _adr_0002_inputs() if all(c.isalnum() or c == "_" for c in n)]
        self.assertEqual(plain, _ADR_0002_PLAIN)

    def test_splits_plain_identifiers_like_adr_0002_rule_1(self):
        # On letters, digits and "_", ADR 0001 and ADR 0002 rule 1 agree: a run of "_" ends
        # a word, leading and trailing ones are dropped, and case changes do not split.
        for name in _ADR_0002_PLAIN:
            with self.subTest(name=name):
                self.assertEqual(words(name), [part for part in re.split("_+", name) if part])


if __name__ == "__main__":
    unittest.main()
