<!-- ADR 0001: the word rule of textkit.counts.word_count (plan task T1.5). -->
# 0001. What counts as a word in `word_count`

## Context

`textkit.counts.word_count(text) -> int` (plan task T1.5) needs a rule for what a word is.
`str.split()` is the obvious choice but counts punctuation as words (`"a - b"` gives 3,
`"!!!"` gives 1). The plan also reuses this rule later: T1.10 moves it into a private
`textkit/_tokens.words` and asserts it against the case table at the end of this ADR, so the
rule must be exact and expressible as one regular expression.

The hard cases are hyphenated words, numbers and apostrophes, which a "letters only" rule
splits and a "non-space" rule over-counts.

## Decision

A **word** is a maximal match of

```
[^\W_]+(?:(?:[-'’]|(?<=\d)[.,](?=\d))[^\W_]+)*
```

that is:

1. **Core characters** are letters and digits of any script: Python's Unicode `\w` minus `_`.
   So `"naïve"`, `"año"` and `"2026"` are words; `_` is a separator (`"snake_case"` is two
   words), because in prose it is markup or an identifier, not part of a word.
2. **Hyphens join** two runs when there is exactly one: `"well-known"` and `"R2-D2"` are one
   word each. A doubled hyphen (`"rock--roll"`, the ASCII stand-in for an em dash) separates,
   and so does a hyphen with a space on either side (`"a - b"` is two words).
3. **Apostrophes join** two runs when there is exactly one, ASCII `'` or typographic `’`
   (U+2019): `"don't"` and `"don’t"` are one word. Leading or trailing apostrophes (quotes,
   plural possessives such as `"dogs'"`) are not part of the word but do not create one.
4. **Numbers** are words. A `.` or `,` between two digits joins them, so decimals and
   thousands separators stay one number (`"3.14"`, `"1,000,000"`). Anywhere else, `.` and `,`
   are punctuation (`"end.Start"` is two words).
5. **Everything else separates**: whitespace of any kind and length (spaces, tabs, newlines),
   all other punctuation and symbols. Input with no core character counts `0`.

Non-`str` input raises `TypeError`; there is no Unicode normalization (it is not needed,
since combining marks are part of `\w`).

## Consequences

- Prose counts match what a reader expects for contractions, compounds and numbers, which
  `str.split()` does not.
- One regular expression defines the rule, so T1.10 can move it into `textkit/_tokens.py`
  unchanged and `word_count` becomes `len(words(text))`.
- Edge cases the rule settles in a possibly surprising way: `"_"` separates; a version string
  like `"1.2.3"` is one word (each `.` is between digits); `"e.g."` is two words; `"U.S."` is
  two words. Changing any of them means amending this ADR and its table.
- `tests/test_counts.py` tests every row below and checks that this table and the tests list
  the same cases, so the two cannot drift apart silently.

## Cases

Inputs are Python string literals.

| Input | Count |
|-------|-------|
| `""` | 0 |
| `"   \n\t  "` | 0 |
| `"!!! ... ---"` | 0 |
| `"hello"` | 1 |
| `"Hello, world!"` | 2 |
| `"well-known"` | 1 |
| `"R2-D2"` | 1 |
| `"rock--roll"` | 2 |
| `"a - b"` | 2 |
| `"don't"` | 1 |
| `"don’t"` | 1 |
| `"'quoted' dogs'"` | 2 |
| `"42"` | 1 |
| `"3.14"` | 1 |
| `"1,000,000"` | 1 |
| `"end.Start"` | 2 |
| `"a  b\n\nc\td"` | 4 |
| `"snake_case"` | 2 |
| `"naïve café"` | 2 |
| `"año 2026"` | 2 |
