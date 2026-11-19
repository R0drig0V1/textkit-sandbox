<!-- ADR 0001: the word rule of textkit.counts.word_count (and later textkit._tokens.words). -->
# 0002. What counts as a word

## Context

`word_count(text)` (plan task T1.5) needs a definition of "word". The simple choices are
wrong in ways people notice: `len(text.split())` counts `"!!!"` and `"-"` as words, and
`\w+` splits `"don't"` and `"well-known"` in two and `"3.14"` into two numbers. The rule
is also shared: T1.10 moves it into `textkit._tokens.words`, T2.1 (`reading_time`) builds on
it, and T1.10's tests assert every row of the table below, so it has to be exact.

## Decision

A **word** is a maximal run of word characters, where:

1. **Alphanumerics** start and continue a word: any character with `str.isalnum()` true, in
   any script, digits included. **Numbers are words** (`"42"` is one word).
2. **Combining marks** (Unicode category `M*`) continue the word they follow, so text in
   decomposed form (NFD) counts like composed text, and scripts whose vowel signs are marks
   are not split. No normalization is applied to the input.
3. **Hyphens and apostrophes** join: a single `-`, `'` or `’` (U+2019) directly between a
   word character and an alphanumeric belongs to the word (`"well-known"`, `"don't"`,
   `"don’t"`). Leading or trailing ones do not (`"'tis"`, `"dogs'"`), and two in a row
   (`"a--b"`, a dash) separate.
4. **Decimal and thousands separators** join digits: a single `.` or `,` directly between two
   decimal digits (`str.isdecimal()`) belongs to the word (`"3.14"`, `"1,000,000"`).
5. **Everything else separates**: whitespace of any kind, punctuation, symbols and `_`.

## Consequences

- Hyphenated compounds and contractions count once, as a reader would count them.
- `_` separates, so `snake_case` is two words: `word_count` is for prose, not identifiers.
- `.` only joins digits, so abbreviations with periods count per letter (`"U.S.A."` is 3).
- `"1, 2, 3"` is three words because the comma is followed by a space, not a digit.
- Other dash characters (U+2010 to U+2015) separate; only ASCII `-` joins.
- Changing this rule changes `word_count`, `reading_time` and `_tokens.words` together; it
  needs a new ADR that supersedes this one and an update of the table and its tests.

## Table of cases

Tested row by row in `tests/test_counts.py` (`ADR_0001_CASES`, same order).

| Input (Python literal) | Count | Why |
|------------------------|-------|-----|
| `"well-known"` | 1 | hyphen between letters joins |
| `"42"` | 1 | numbers are words |
| `"3.14"` | 1 | `.` between digits joins |
| `"1,000,000"` | 1 | `,` between digits joins |
| `"don't"` | 1 | apostrophe between letters joins |
| `"don’t"` | 1 | typographic apostrophe joins too |
| `"the dogs' bowls"` | 3 | trailing apostrophe is not part of the word |
| `"'tis"` | 1 | leading apostrophe is not part of the word |
| `""` | 0 | empty text |
| `"!!! ... ?"` | 0 | punctuation only |
| `"  one \n\n two\t three  "` | 3 | runs of spaces, newlines and tabs separate once |
| `"a--b"` | 2 | two hyphens in a row separate |
| `"well - known"` | 2 | a lone hyphen between spaces is not a word |
| `"snake_case"` | 2 | `_` separates |
| `"U.S.A."` | 3 | `.` joins only digits |
| `"1, 2, 3"` | 3 | `,` followed by a space separates |
| `"naïve café"` | 2 | non-ASCII letters are word characters |
| `"naïve café"` | 2 | combining marks (NFD) stay in their word |
