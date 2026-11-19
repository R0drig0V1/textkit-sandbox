<!-- ADR 0001: the word rule shared by word_count (T1.5) and, later, textkit/_tokens.py (T1.10). -->
# 0001. What counts as a word

- Status: accepted
- Task: T1.5 (`word_count` in `textkit/counts.py`)

## Context

`word_count(text) -> int` needs a definition of "word". `str.split()` is the obvious choice,
but it counts punctuation-only tokens (`"a - b"` gives 3) and attaches punctuation to words.
A regex such as `\w+` splits `"don't"` and `"well-known"` in two and treats `_` as a letter.
The rule is not local to one function: T1.10 extracts it into `textkit/_tokens.py` as
`words(text)` and reuses it for `to_snake_case`, and T1.6, T2.1 and T2.2 build on the same
module. So the rule has to be stated exactly, with cases a test can check, and changing it
later changes every count in textkit.

## Decision

A **word** is a maximal run of *word characters*, where a *joiner* placed between two word
characters keeps the run going.

- **Word characters** are the characters whose Unicode general category is a letter (`L*`),
  a number (`N*`) or a combining mark (`M*`). This covers every script, digits, and
  decomposed (NFD) accents, so `"café"` is one word just like `"café"`.
- **Joiners** (exactly one character, with a word character on each side):
  - `-` (hyphen-minus): hyphenated words are one word (`"well-known"`,
    `"state-of-the-art"`).
  - `'` and `’` (U+2019): contractions and possessives are one word (`"don't"`,
    `"o’clock"`).
  - `.` and `,`, **only between two decimal digits**: numbers with decimals or thousands
    separators are one word (`"3.14"`, `"1,000,000"`, `"v1.2"`).
- **Everything else separates words**: whitespace of any kind, any other punctuation,
  symbols, and `_`. A joiner that is not between two word characters is a separator too, so
  a doubled hyphen, a dash between spaces, or quotes around a word do not join or count
  (`"well--known"` is two words, `"'quoted'"` is one).
- **Numbers are words.** `"42"` counts as one word, like any other run.
- `word_count` raises `TypeError` for anything that is not a `str`.

## Consequences

- Counts match what a reader expects for ordinary prose in languages that put spaces
  between words, including curly apostrophes and NFD input.
- Scripts written without spaces (Chinese, Japanese, Thai) are not segmented: `"日本語"` is
  one word. Doing better needs a dictionary, which the standard-library-only rule excludes.
- `_` separates, so `"snake_case"` is two words. T1.10 relies on this when it reuses the rule
  for identifiers.
- Symbols are separators, so `"C++"` is the word `C`, and an e-mail address or URL counts as
  several words (`"me@example.com"` is 3).
- Only `-` joins; other hyphen and dash characters (U+2010, en and em dashes) separate. Adding
  one later is a change to this ADR and to every count.
- The rule is written as a character scan, not a regex, because Python's `re` has no
  `\p{M}` class to keep combining marks inside words.

## Cases

Inputs are Python string literals. `tests/test_counts.py` checks every row, and checks that
this table and its own list of cases are the same.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"   \n\t "` | 0 | whitespace only |
| `"!!! ... ?"` | 0 | punctuation only |
| `"hello world"` | 2 | plain words |
| `"  one \n\n two\tthree  "` | 3 | several spaces, newlines and a tab |
| `"well-known"` | 1 | hyphenated word |
| `"state-of-the-art design"` | 2 | several hyphens in one word |
| `"well--known"` | 2 | a doubled hyphen separates |
| `"pages 10 - 12"` | 3 | a hyphen between spaces separates |
| `"don't"` | 1 | apostrophe inside a word |
| `"don’t"` | 1 | typographic apostrophe U+2019 |
| `"rock 'n' roll"` | 3 | leading and trailing apostrophes separate |
| `"'quoted'"` | 1 | quotes around a word |
| `"42"` | 1 | a number |
| `"3.14"` | 1 | decimal point between digits |
| `"1,000,000 people"` | 2 | thousands separators between digits |
| `"v1.2"` | 1 | `.` between digits inside a mixed run |
| `"end.Next"` | 2 | `.` between letters separates |
| `"a,b"` | 2 | `,` between letters separates |
| `"snake_case"` | 2 | `_` separates |
| `"C++ and C#"` | 3 | symbols separate |
| `"naïve café"` | 2 | precomposed accents |
| `"Nañdú"` | 1 | decomposed (NFD) accents |
| `"日本語"` | 1 | no segmentation for scripts without spaces |
