<!-- 0002-what-counts-as-a-word: the word rule used by textkit.counts.word_count (and later textkit._tokens.words). -->
# 0002. What counts as a word

## Context

`textkit.counts.word_count(text)` (plan task T1.5) needs a precise definition of a word.
Splitting on whitespace (`len(text.split())`) is the obvious answer, but it counts
punctuation-only tokens (`"a - b"` would be 3) and glues punctuation to words. The cases
readers will ask about are hyphenated words, numbers and apostrophes. T1.10 will later move
this rule into a shared tokenizer (`textkit._tokens.words`) and must reproduce it exactly, so
the rule has to be stated without reference to the implementation, and every case below is a
test.

## Decision

A **word** is a maximal run of *word characters*, optionally joined by single *joiners*:

1. **Word characters** are the characters for which `str.isalnum()` is true (Unicode letters
   and digits, so `ñ`, `é` and `²` count), plus combining marks (Unicode category `M*`) that
   follow a word character, so decomposed (NFD) text such as `"Ñandú"` stays one
   word. A combining mark with no word character before it is a separator.
2. **Joiners** keep a word together only when they have a word character on *both* sides:
   - a hyphen-minus `-` (`well-known`, `state-of-the-art`, `x-ray`);
   - an apostrophe, ASCII `'` or typographic `’` (U+2019) (`don't`, `O’Neill`);
   - a `.` or `,` between two decimal digits (`str.isdecimal()`), so numbers like `3.14`
     and `1,000` are one word.

   Two joiners in a row (`a--b`, `a'-b`) do not join: the word ends before them.
3. **Everything else separates words**: whitespace of any kind, other punctuation, the
   underscore (`snake_case` is two words), en and em dashes (`2010–2020` is two words), and
   joiners at the edge of a word (`-leading`, `dogs'`, `’n’`).
4. `word_count(text)` is the number of words. Text that is not a `str` raises `TypeError`.

Hyphenated compounds and contractions are one word because that is what a reader counts and
what word processors report. Underscores separate because `textkit` treats identifiers as
several words (the case-conversion helpers of T1.7 split them). No Unicode normalization is
applied; NFC and NFD forms of the same text give the same count because of rule 1.

## Consequences

- `word_count` differs from `len(text.split())` whenever punctuation stands alone or glues
  two words together (`"hello,world"` is 2 words, `"a - b"` is 2).
- Abbreviations with dots split: `e.g.` is 2 words. Accepted: rare in the texts this helper
  targets, and handling them would need a dictionary.
- Signs are not part of numbers (`-5` counts the word `5`), which does not change the count.
- Scripts without spaces between words (Chinese, Japanese, Thai) count a whole run as one
  word. Out of scope: it would need a segmentation dictionary.
- T1.10's `words(text)` must return exactly the words of this rule; the table below is its
  acceptance test as well.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that this
table and its own case list stay identical.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"   \n\t  "` | 0 | whitespace only |
| `"!!! ... ?"` | 0 | punctuation only |
| `"hello world"` | 2 | plain words |
| `"well-known"` | 1 | hyphenated word |
| `"state-of-the-art design"` | 2 | several hyphens inside one word |
| `"a - b"` | 2 | a free-standing hyphen is not a word |
| `"a--b"` | 2 | two joiners in a row do not join |
| `"-leading and trailing-"` | 3 | edge hyphens separate |
| `"2010–2020"` | 2 | en dash separates |
| `"don't"` | 1 | word with an apostrophe |
| `"O’Neill"` | 1 | typographic apostrophe |
| `"the dogs' bowls"` | 3 | trailing apostrophe separates |
| `"rock ’n’ roll"` | 3 | edge apostrophes separate |
| `"42"` | 1 | a number |
| `"3.14 and 1,000"` | 3 | decimal point and thousands separator between digits |
| `"v2.0"` | 1 | `.` between two digits joins, whatever comes before them |
| `"page 3."` | 2 | `.` after a digit with no digit after it separates |
| `"e.g."` | 2 | abbreviation dots separate |
| `"end."` | 1 | trailing punctuation is not a word |
| `"hello,world"` | 2 | punctuation between letters separates |
| `"snake_case"` | 2 | underscore separates |
| `"one  two\n\nthree\tfour\r\n"` | 4 | several spaces and newlines |
| `"Ñandú café"` | 2 | non-ASCII letters (NFC) |
| `"Ñandú"` | 1 | combining marks (NFD) stay in the word |
| `"́abc"` | 1 | a leading combining mark separates |
