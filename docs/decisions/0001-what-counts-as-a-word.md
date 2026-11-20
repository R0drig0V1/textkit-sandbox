<!-- ADR 0001: the word rule of word_count (T1.5), reused by the shared tokenizer (T1.10). -->
# 0001. What counts as a word

## Context

`word_count(text)` (T1.5, `textkit/counts.py`) needs a rule for what a word is. Splitting on
whitespace is not enough: it counts `"!!!"` and a lone `-` as words and glues punctuation to
words. Later tasks build on the same rule: `char_freq` (T1.6) sits in the same module,
`reading_time` (T2.1) is computed from `word_count`, `sentence_count` (T2.2) shares the
module, and T1.10 reimplements this rule in `textkit/_tokens.py` as `words(text)` and checks
it row by row against the table below. So the rule has to be exact enough for two
independent implementations to agree on every input.

## Decision

The definitions use Python's `str` methods and `unicodedata`, applied to code points, with
no Unicode normalization:

- **Word character**: `ch.isalnum()` is true (Unicode letters and digits of any script).
- **Mark**: `unicodedata.category(ch)` starts with `"M"` (combining marks such as U+0301).
- **Joiner**: `-` (U+002D), `'` (U+0027) or `’` (U+2019).
- **Digit joiner**: `.` or `,`.

A word is a maximal substring that:

1. starts with a word character;
2. continues through word characters and marks;
3. also continues through **one** joiner, when the character before it is part of the word
   and the character after it is a word character (`well-known`, `don't`, `rock'n'roll`);
4. also continues through **one** digit joiner, when the character before it and the
   character after it are both decimal digits (`ch.isdecimal()`): `3.14`, `1,000,000`.

Every other character separates words: whitespace of any kind, other punctuation, symbols,
`_`, the en and em dashes, a joiner at either end of a word or doubled (`--`), a digit joiner
not between two digits. `word_count` returns the number of words; `""` and text with no word
character give 0.

Consequences of the rule worth stating, because they are where readers disagree:

- **Hyphenated words** are one word (`"state-of-the-art"` is 1). A spaced or doubled hyphen
  is a separator (`"a - b"` and `"a--b"` are 2).
- **Numbers** are words. `.` and `,` inside a number keep it whole; a sign or unit symbol is
  not part of it (`"-5"`, `"$5"`, `"5%"` are 1). A trailing full stop ends the word
  (`"1."` is 1). Digits and letters together are one word (`"hello123"`, `"v1.2"`).
- **Apostrophes** (straight and typographic) inside a word keep it whole (`"don't"` is 1);
  leading or trailing ones, as in quotes or plural possessives, are dropped
  (`"students'"` is 1).
- **Abbreviations, URLs and e-mail addresses** get no special case: `.` between letters
  separates (`"e.g."` is 2, `"example.com"` is 2). Sentence-level questions belong to T2.2.
- **Identifiers**: `_` separates (`"snake_case"` is 2); case changes do not
  (`"camelCase"` is 1). Splitting identifiers is the job of `to_snake_case` (T1.7).
- **Accents**: precomposed (NFC) and decomposed (NFD) text count the same, because marks
  continue a word. A mark with no word before it is not a word.
- **Scripts without spaces** (Chinese, Japanese, Thai) are not segmented: a run of their
  letters is one word.

## Consequences

- `word_count` is a single left-to-right scan with one character of look-behind and one of
  look-ahead; no regular expression, since `re` has no class for Unicode marks.
- T1.10's `words(text)` must return exactly the substrings defined above; its tests and
  `tests/test_counts.py` both check every row of the table below.
- Changing the rule later changes `word_count`, `reading_time` and anything built on
  `words`; it needs a new ADR that supersedes this one.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that
its list of cases equals this table.

| Input | Count |
|-------|-------|
| `""` | 0 |
| `"hello"` | 1 |
| `"Hello, world!"` | 2 |
| `"well-known"` | 1 |
| `"state-of-the-art design"` | 2 |
| `"a - b"` | 2 |
| `"a--b"` | 2 |
| `"-dash- start"` | 2 |
| `"a—b"` | 2 |
| `"42"` | 1 |
| `"3.14"` | 1 |
| `"1,000,000"` | 1 |
| `"-5"` | 1 |
| `"$5 or 5%"` | 3 |
| `"Chapter 1."` | 2 |
| `"1, 2, 3"` | 3 |
| `"v1.2"` | 1 |
| `"hello123"` | 1 |
| `"don't"` | 1 |
| `"don’t"` | 1 |
| `"rock'n'roll"` | 1 |
| `"the students' books"` | 3 |
| `"'quoted'"` | 1 |
| `"e.g."` | 2 |
| `"example.com"` | 2 |
| `"snake_case"` | 2 |
| `"camelCase"` | 1 |
| `"naïve café"` | 2 |
| `"Ñandú"` | 1 |
| `"́"` | 0 |
| `"日本語"` | 1 |
| `"!!! ... ?"` | 0 |
| `" \n\t "` | 0 |
| `"  a \n\n b\t c  "` | 3 |
