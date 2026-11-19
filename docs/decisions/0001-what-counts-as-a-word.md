<!-- ADR 0001: the word rule behind word_count and every helper built on it. -->
# 0001: What counts as a word

## Context

`word_count` (T1.5, `textkit/counts.py`) needs a word rule. Later work builds on it:
`reading_time` (T2.1) counts with `word_count`, `sentence_count` (T2.2) sits in the same
module, and the shared tokenizer `textkit._tokens.words` (T1.10) must implement this rule
exactly and is tested against the case table below. So the rule has to be precise enough
to be reimplemented from this page alone.

The obvious candidate, `len(text.split())`, counts punctuation as words (`"... !!!"` gives
2) and glues punctuation to words. Treating every non-alphanumeric character as a separator
fixes that but splits `"well-known"`, `"don't"` and `"3.14"` into two words each, which no
reader would expect. The three questions are hyphenated words, apostrophes and numbers.

## Decision

A **word** is a maximal span of `text` built by these rules, scanning left to right:

1. A word **starts** at a character for which `str.isalnum()` is true (letters and digits
   of any script, so `"naïve"` and `"日本語"` work).
2. It **continues** over further `str.isalnum()` characters and over **combining marks**
   (Unicode category `M*`), so NFD input counts the same as NFC (`"Ñandú"` is
   one word). A combining mark never starts a word.
3. **Apostrophes and hyphens join.** An apostrophe (`'` U+0027 or `’` U+2019) or a hyphen
   (`-` U+002D) continues the word only when a word is open and the next character is
   `str.isalnum()`. So `"don't"`, `"rock'n'roll"` and `"state-of-the-art"` are one word;
   leading or trailing apostrophes and hyphens (`"'quoted'"`, `"dogs'"`, `"-5"`), doubled
   hyphens (`"a--b"`) and spaced hyphens (`"well - known"`) are separators. Dashes other
   than U+002D (`—`, `–`) always separate.
4. **Numbers keep their separators.** A `.` or `,` continues the word only when the
   character before it and the character after it are both `str.isdecimal()`. So `"3.14"`,
   `"1,000,000"` and `"v2.0"` are one word; `"1, 2, 3"` is three and `"end.Start"` two.
5. **Everything else separates**: whitespace of any kind and any amount, other punctuation,
   symbols (`%`, `#`, `+`, `@`) and the underscore (`"snake_case"` is two words).

`word_count(text)` is the number of words. A non-`str` argument raises `TypeError`.

Why these choices:

- Joining on an apostrophe or hyphen only when a letter or digit follows is the smallest
  rule that keeps contractions and compounds whole while still treating quotes and dashes
  as punctuation.
- Number separators are restricted to digit-digit so that sentence punctuation
  (`"end.Start"`, `"1, 2"`) still separates; this also keeps `sentence_count` (T2.2) free
  to treat `.` between letters as a sentence boundary candidate.
- `_` separates because it is not prose; it also matches how `snake_case` identifiers split
  into words, which T1.10 may rely on when sharing the tokenizer with `to_snake_case`.

## Consequences

- Scripts written without spaces (Chinese, Japanese, Thai) count each unbroken run as one
  word. Real segmentation needs a dictionary, which the standard-library-only rule rules out.
- Abbreviations with periods between letters split: `"e.g."` is two words. This slightly
  over-counts for `reading_time`, which is acceptable; T2.2 decides separately how such
  abbreviations affect sentences.
- Symbols are dropped, not counted: `"C++ and C#"` is three words, `"50%"` one.
- Changing any rule changes `word_count`, `reading_time` and `_tokens.words` together; such
  a change needs a new ADR that supersedes this one and an update of the table below and
  of `tests/test_counts.py` and `tests/test_tokens.py`.

## Cases

Inputs are Python string literals. `tests/test_counts.py` (`WordCountTest`) asserts every
row.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty |
| `"  \n\t  "` | 0 | whitespace only |
| `"... !!! ?"` | 0 | punctuation only |
| `"hello"` | 1 | one plain word |
| `"Hello, world!"` | 2 | punctuation next to words separates |
| `"one  two\n\nthree\tfour"` | 4 | several spaces, newlines and tabs are one separator |
| `"well-known"` | 1 | hyphenated word (rule 3) |
| `"state-of-the-art"` | 1 | several hyphens (rule 3) |
| `"well - known"` | 2 | spaced hyphen separates |
| `"-leading trailing-"` | 2 | leading and trailing hyphens separate |
| `"a--b"` | 2 | a doubled hyphen separates |
| `"word—word"` | 2 | an em dash separates |
| `"don't"` | 1 | apostrophe (rule 3) |
| `"don’t"` | 1 | typographic apostrophe (rule 3) |
| `"rock'n'roll"` | 1 | several apostrophes (rule 3) |
| `"'quoted'"` | 1 | surrounding quotes separate |
| `"dogs' bowls"` | 2 | trailing apostrophe separates |
| `"42"` | 1 | a number |
| `"3.14"` | 1 | decimal point between digits (rule 4) |
| `"1,000,000"` | 1 | thousands separators between digits (rule 4) |
| `"1, 2, 3"` | 3 | comma followed by a space separates |
| `"v2.0"` | 1 | letters and digits mix; `.` between digits (rule 4) |
| `"end.Start"` | 2 | `.` between letters separates |
| `"e.g."` | 2 | abbreviation splits |
| `"snake_case"` | 2 | underscore separates (rule 5) |
| `"naïve café"` | 2 | non-ASCII letters (rule 1) |
| `"Ñandú"` | 1 | combining marks continue a word (rule 2) |
| `"日本語"` | 1 | an unbroken non-spaced run is one word |
| `"C++ and C#"` | 3 | symbols separate and are not counted |
| `"50%"` | 1 | a symbol after a number separates |
| `"-5"` | 1 | a leading minus is not part of the number |
