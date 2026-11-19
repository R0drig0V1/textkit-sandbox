<!-- ADR 0001: the word rule behind word_count and the shared tokenizer. -->
# 0001. What counts as a word

## Context

`word_count` (T1.5) needs a definition of "word", and later work reuses it: `reading_time`
(T2.1) is computed from `word_count`, `sentence_count` (T2.2) lives next to it, and the shared
tokenizer `textkit/_tokens.py` (T1.10) must implement exactly this rule. "Split on whitespace"
is not enough: it counts `"!!!"` as a word and `"Hello,world"` as one. The open questions are
hyphenated words, numbers with separators, apostrophes (straight and typographic), and
non-ASCII text (accents in NFC and NFD form, scripts without spaces).

## Decision

A **word** is found by scanning the text left to right:

1. A word **starts** at a character `c` with `c.isalnum()` true (Unicode letters and digits,
   so `é`, `ñ`, `日` and `²` qualify; `_` does not).
2. A word **continues** over:
   - alphanumeric characters (`c.isalnum()`);
   - combining marks (`unicodedata.category(c)` starting with `M`), so that NFD text
     (`"naïve"`) counts the same as NFC text (`"naïve"`); a mark never starts a word;
   - a **hyphen** (`-` U+002D or `‐` U+2010) or an **apostrophe** (`'` U+0027 or `’` U+2019)
     that is immediately followed by an alphanumeric character;
   - a **`.` or `,`** that is immediately preceded and followed by a decimal digit
     (`str.isdecimal`), so a number such as `3.14` or `1,000,000` is one word.
3. Any other character **ends** the current word: whitespace, other punctuation (including
   `_`, `—`, `–`, `/`, `+`), symbols and emoji. A joiner that does not meet its condition
   (a leading, trailing or doubled hyphen or apostrophe; a `.` next to a letter) is also a
   separator and is not part of any word.

Words are maximal: the count is the number of such runs. Only one joiner is accepted
between two word characters, so `a--b` is two words. There is no dictionary or language
segmentation: a run of CJK characters is one word, and `U.S.A.` is three.

`word_count` raises `TypeError` for anything that is not a `str`.

## Consequences

- Prose counts the way a reader expects for English and other space-separated languages:
  contractions, possessives, compound words and numbers are one word each; punctuation and
  emoji are never words.
- `snake_case` is two words and `camelCase` is one: the rule is for prose, not identifiers.
  T1.10 must take this into account where it reuses the tokenizer for `to_snake_case`.
- Ranges and dates written with a hyphen (`10-12`, `2026-11-19`) are one word, and so is
  `1,2,3`; abbreviations with dots (`e.g.`, `U.S.A.`) are split at each dot.
- Languages written without spaces (Chinese, Japanese, Thai) are undercounted. Supporting them
  would need a segmentation library, which the standard-library-only rule excludes.
- Changing the rule later changes `word_count`, `reading_time` and the shared tokenizer at
  once; it needs a new ADR that supersedes this one and an update of the table below.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that this
table and its own list of cases are the same.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"hello"` | 1 | one plain word |
| `"Hello, world!"` | 2 | punctuation separates and is not a word |
| `"  one   two \n\n three\t"` | 3 | several spaces, newlines and tabs separate like one space |
| `"!!! ... ---"` | 0 | punctuation only |
| `"well-known"` | 1 | hyphen between letters joins |
| `"state-of-the-art design"` | 2 | several hyphens, each between letters |
| `"a - b"` | 2 | a hyphen with spaces around it is not a word |
| `"a--b"` | 2 | a doubled hyphen separates |
| `"-5"` | 1 | a leading hyphen is dropped |
| `"1-2"` | 1 | hyphen between digits joins |
| `"don't"` | 1 | straight apostrophe between letters joins |
| `"don’t"` | 1 | typographic apostrophe (U+2019) joins too |
| `"rock'n'roll"` | 1 | several apostrophes, each between letters |
| `"'quoted' students'"` | 2 | leading and trailing apostrophes are dropped |
| `"e-mail's"` | 1 | hyphen and apostrophe in one word |
| `"42"` | 1 | a number is a word |
| `"3.14 and 1,000,000"` | 3 | `.` and `,` between digits join |
| `"v2.0"` | 1 | `.` between digits joins after a letter-digit run |
| `"U.S.A."` | 3 | `.` between letters separates |
| `"end. Next"` | 2 | a sentence-ending dot separates |
| `"x2 3x"` | 2 | letters and digits mix within a word |
| `"C++"` | 1 | symbols are not words |
| `"snake_case"` | 2 | underscore separates |
| `"well—maybe"` | 2 | an em dash separates |
| `"naïve café"` | 2 | accented letters (NFC) are letters |
| `"naïve"` | 1 | a combining mark (NFD) continues the word |
| `"́"` | 0 | a combining mark alone is not a word |
| `"日本語"` | 1 | no segmentation of scripts without spaces |
| `"🙂"` | 0 | emoji are not words |
