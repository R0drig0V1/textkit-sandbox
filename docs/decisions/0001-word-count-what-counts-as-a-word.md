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
RUN(?:(?:[-'’]|(?<=\d)[.,](?=\d))RUN)*      where RUN = (?:[^\W_]\p{M}*)+
```

(`\p{M}` is every Unicode mark, categories Mn, Mc and Me; Python's `re` has no `\p{...}`, so
the code generates that class from `unicodedata`), that is:

1. **Core characters** are letters and digits of any script: Python's Unicode `\w` minus `_`.
   So `"naïve"`, `"año"` and `"2026"` are words; `_` is a separator (`"snake_case"` is two
   words), because in prose it is markup or an identifier, not part of a word.
2. **Combining marks** (Unicode category M) belong to the word when they follow a core
   character or another mark of it. Python's `\w` does **not** match them (it matches what
   `str.isalnum()` accepts, plus `_`, and marks are not alphanumeric), so without this rule
   decomposed (NFD) text splits words (`"cafe\u0301"` would be two) and so do scripts whose
   vowel signs are marks (Devanagari `"हिन्दी"` would be three). A mark with no core character
   before it (after a space or punctuation) is not a word and not counted.
3. **Hyphens join** two runs when there is exactly one: `"well-known"` and `"R2-D2"` are one
   word each. A doubled hyphen (`"rock--roll"`, the ASCII stand-in for an em dash) separates,
   and so does a hyphen with a space on either side (`"a - b"` is two words).
4. **Apostrophes join** two runs when there is exactly one, ASCII `'` or typographic `’`
   (U+2019): `"don't"` and `"don’t"` are one word. Leading or trailing apostrophes (quotes,
   plural possessives such as `"dogs'"`) are not part of the word but do not create one.
5. **Numbers** are words. A `.` or `,` between two digits joins them, so decimals and
   thousands separators stay one number (`"3.14"`, `"1,000,000"`). Anywhere else, `.` and `,`
   are punctuation (`"end.Start"` is two words).
6. **Everything else separates**: whitespace of any kind and length (spaces, tabs, newlines),
   all other punctuation and symbols. Input with no core character counts `0`.

Non-`str` input raises `TypeError`. No Unicode normalization is applied: rule 2 already makes
NFC and NFD forms of the same text count the same, and it also covers stacked marks and marks
with no precomposed form, which normalizing to NFC first would not.

## Consequences

- Prose counts match what a reader expects for contractions, compounds and numbers, which
  `str.split()` does not.
- The mark class follows the Unicode version of the running Python's `unicodedata`, the same
  database `\w` uses, rather than hand-written ranges that would go stale. Building it scans
  every code point (about 0.1 s), so it is done once, on the first call, not at import.
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
| `"nai\u0308ve cafe\u0301"` | 2 |
| `"N\u0303andu\u0301"` | 1 |
| `"\u0939\u093f\u0928\u094d\u0926\u0940"` | 1 |
| `"\u0301 a"` | 1 |
