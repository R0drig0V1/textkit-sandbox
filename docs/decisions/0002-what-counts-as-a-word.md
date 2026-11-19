<!-- ADR 0002: the word rule shared by word_count (T1.5), the words tokenizer (T1.10) and the tools built on them. -->
# 0002. What counts as a word

- Status: accepted
- Task: T1.5 (`word_count` in `textkit/counts.py`)
- Used by: T1.6, T1.10 (`textkit._tokens.words` must implement this rule exactly), T2.1, T2.2

## Context

`word_count(text) -> int` needs a definition of "word". Splitting on whitespace
(`len(text.split())`) is the obvious choice, but it counts punctuation as words (`"a - b"` is
3, `"!!!"` is 1) and cannot be turned into a tokenizer whose tokens are the words themselves
(`"Hello,"` would keep its comma). Matching `\w+` goes too far the other way: it splits
`"well-known"`, `"don't"` and `"3.14"` into two words each and keeps `_` inside words.

The rule has to settle the three cases the plan names (hyphenated words, numbers,
apostrophes), handle any script (textkit is not ASCII-only outside `slugify`), and be precise
enough that T1.10 can write `words(text) -> list[str]` from this page alone and get the same
list for every input. `reading_time` (T2.1) counts with it and `sentence_count` (T2.2) lives
next to it.

## Decision

### Character classes

Every character of `text` falls in exactly one class, tested in this order:

| Class | Characters |
|-------|------------|
| **A** (alphanumeric) | `c.isalnum()` is true: letters and digits of any script, including `²`, `一` |
| **M** (mark) | `unicodedata.category(c)` starts with `"M"` (Mn, Mc, Me): combining marks |
| **J** (joiner) | `-` U+002D, `‐` U+2010, `‑` U+2011 (hyphens); `'` U+0027, `’` U+2019 (apostrophes); `.` U+002E |
| **C** (digit comma) | `,` U+002C |
| **S** (separator) | everything else: whitespace, other punctuation, symbols, `_`, en dash U+2013, em dash U+2014 |

"Decimal digit" below means `c.isdecimal()` is true.

### The rule

A word is a maximal substring of the form

```
word    = segment ( link segment )*
segment = A ( A | M )*
link    = J            -- exactly one joiner
        | C            -- exactly one comma, only if the character before it and the
                          character after it are both decimal digits
```

Equivalently, as a left-to-right scan (this is the reference implementation,
`textkit.counts._words`):

1. Skip characters until one in class **A**; that character starts a word. A character of
   any other class, **M** included, never starts a word.
2. Extend the word over every following **A** or **M** character.
3. At a **J** character: if the next character is in **A**, add both to the word and go to
   step 2; otherwise the word ends before the joiner.
4. At a **C** character: if the previous character is a decimal digit and the next character
   is a decimal digit, add both to the word and go to step 2; otherwise the word ends before
   the comma.
5. Any other character ends the word; go to step 1 from there.

`words(text)` is the list of these substrings in order, unchanged (no case folding, no
normalization); `word_count(text) == len(words(text))`.

What follows from it:

- **Hyphenated words** are one word (`"well-known"`, `"state-of-the-art"`, `"COVID-19"`). A
  hyphen not between a word character and an alphanumeric (`"a - b"`, `"-5"`, `"5-"`,
  `"well--known"`) separates and is not part of any word.
- **Numbers** are words. A period between two alphanumerics and a comma between two decimal
  digits keep a number whole (`"3.14"`, `"1,000,000"`, `"v2.0.1"`). Signs, currency and
  percent symbols are not part of the word (`"-5"` -> `5`, `"$5"` -> `5`, `"50%"` -> `50`).
- **Apostrophes** inside a word keep it whole (`"don't"`, `"O’Brien"`, with the ASCII or the
  typographic apostrophe). Leading and trailing apostrophes are dropped, which also strips
  single quotes used as quotation marks (`"'n'"` -> `n`, `"students'"` -> `students`).
- **A period** between two alphanumerics joins, so abbreviations keep their inner periods but
  lose the last one (`"e.g."` -> `e.g`, one word) and an ellipsis with no spaces separates
  (`"wait...what"` is two words).
- **Combining marks** stay with the letter they follow, so NFC and NFD input count the same
  (`"café"` is one word either way) and scripts with vowel signs (Devanagari `"हिन्दी"`) are
  not cut apart.
- **Scripts written without spaces** (Chinese, Japanese) count each run of letters as one word.
  Segmenting them needs a dictionary, which the standard library does not have.
- **`_`** separates (`"snake_case"` is two words). The rule is for prose; identifiers are
  split by `textkit.cases` under its own ADR.

### Case table

Every row is tested in `tests/test_counts.py` (`WordCountTest`), and T1.10 asserts the
**Words** column against `words`. Inputs are Python string literals.

| # | Input | Words | Count | Shows |
|---|-------|-------|-------|-------|
| 1 | `""` | `[]` | 0 | empty text |
| 2 | `"hello"` | `["hello"]` | 1 | one word |
| 3 | `"Hello, world!"` | `["Hello", "world"]` | 2 | punctuation is dropped |
| 4 | `"well-known"` | `["well-known"]` | 1 | hyphenated word |
| 5 | `"state-of-the-art design"` | `["state-of-the-art", "design"]` | 2 | several hyphens |
| 6 | `"well--known"` | `["well", "known"]` | 2 | a double hyphen separates |
| 7 | `"a - b"` | `["a", "b"]` | 2 | a lone hyphen is not a word |
| 8 | `"-5 and 5-"` | `["5", "and", "5"]` | 3 | leading and trailing hyphens are dropped |
| 9 | `"COVID-19"` | `["COVID-19"]` | 1 | hyphen between a letter and a digit |
| 10 | `"42"` | `["42"]` | 1 | number |
| 11 | `"3.14"` | `["3.14"]` | 1 | decimal number |
| 12 | `"1,000,000"` | `["1,000,000"]` | 1 | digit-group commas |
| 13 | `"v2.0.1"` | `["v2.0.1"]` | 1 | version number |
| 14 | `"1, 2"` | `["1", "2"]` | 2 | a comma followed by a space separates |
| 15 | `"a,b"` | `["a", "b"]` | 2 | a comma between letters separates |
| 16 | `"don't"` | `["don't"]` | 1 | word with an apostrophe |
| 17 | `"O’Brien"` | `["O’Brien"]` | 1 | typographic apostrophe |
| 18 | `"rock 'n' roll"` | `["rock", "n", "roll"]` | 3 | leading and trailing apostrophes are dropped |
| 19 | `"the students' books"` | `["the", "students", "books"]` | 3 | possessive plural |
| 20 | `"e.g. this"` | `["e.g", "this"]` | 2 | abbreviation keeps its inner period |
| 21 | `"wait...what"` | `["wait", "what"]` | 2 | an ellipsis separates |
| 22 | `"snake_case"` | `["snake", "case"]` | 2 | `_` separates |
| 23 | `"pages 10–20"` | `["pages", "10", "20"]` | 3 | en dash separates |
| 24 | `"yes—no"` | `["yes", "no"]` | 2 | em dash separates |
| 25 | `"AT&T"` | `["AT", "T"]` | 2 | symbols separate |
| 26 | `"user@example.com"` | `["user", "example.com"]` | 2 | `@` separates, `.` joins |
| 27 | `"!!! ... ?"` | `[]` | 0 | punctuation only |
| 28 | `"  one \n\n two\t three  "` | `["one", "two", "three"]` | 3 | several spaces, newlines and tabs |
| 29 | `" \n\t "` | `[]` | 0 | whitespace only |
| 30 | `"naïve café"` | `["naïve", "café"]` | 2 | precomposed (NFC) letters |
| 31 | `"naïve café"` | `["naïve", "café"]` | 2 | combining marks (NFD) stay in the word |
| 32 | `"́abc"` | `["abc"]` | 1 | a mark cannot start a word |
| 33 | `"हिन्दी"` | `["हिन्दी"]` | 1 | Devanagari vowel signs (Mc, Mn) |
| 34 | `"東京 2026"` | `["東京", "2026"]` | 2 | CJK run without spaces is one word |
| 35 | `"x²"` | `["x²"]` | 1 | superscript digit is alphanumeric |

## Consequences

- `word_count` and the future `words` never count punctuation, symbols or whitespace, and
  return the same result for NFC and NFD input.
- Some counts differ from a word processor's whitespace count: `"AT&T"` and `"and/or"` are two
  words, `"e.g."` is one, `"3.14"` is one, `"10–20"` is two. These are intended and pinned in
  the table.
- A missing space after a period between letters merges two words (`"end.Next"` is one word),
  the price of keeping `"e.g"`, `"example.com"` and `"3.14"` whole.
- Text in scripts without spaces is under-counted (one word per run); fixing it would need a
  segmentation dictionary, outside the standard library.
- Changing the rule later changes `word_count`, `reading_time` and every caller of `words`:
  it needs a new ADR that supersedes this one and an update of the table and its tests.
