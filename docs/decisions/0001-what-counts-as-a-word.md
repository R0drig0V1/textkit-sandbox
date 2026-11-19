<!-- ADR 0001: the word rule behind word_count and the shared tokenizer (T1.5, T1.10). -->
# 0001. What counts as a word

Status: accepted (plan task T1.5).

## Context

`word_count(text)` (T1.5) needs a definition of "word", and more functions will use it:
`reading_time` (T2.1) is built on `word_count`, and the shared tokenizer
`textkit/_tokens.py` `words(text)` (T1.10) must implement this rule *exactly*, with no change
in `word_count`'s results. So the rule has to be precise enough to implement from this page
alone, and it has to say what happens with hyphens, apostrophes, numbers, other punctuation
and non-ASCII text.

Splitting on whitespace (`len(text.split())`) is the simplest rule, but it counts `"—"`,
`"..."` and `"-"` as words and glues punctuation to words (`"world!"`), which a tokenizer
shared with other helpers must not do. A plain `\w+` regex splits `"don't"` and
`"well-known"` in two, and splits decomposed accents (`"e"` + U+0301) off their letter.

## Decision

Every character of the text falls in exactly one class, checked in this order:

| Class | Characters |
|-------|------------|
| digit | `str.isdecimal()` is true: `0`-`9` and the decimal digits of other scripts (`٢`) |
| letter | `str.isalnum()` is true and it is not a digit: letters of any script, and other numerics such as `²` or `Ⅻ` |
| mark | Unicode general category `M*` (`Mn`, `Mc`, `Me`): combining accents, Indic vowel signs |
| joiner | U+002D `-`, U+2010 `‐`, U+2011 non-breaking hyphen, U+0027 `'`, U+2019 `’` |
| number separator | U+002E `.` and U+002C `,` |
| other | everything else: whitespace, all other punctuation (including `_`, en and em dashes, `/`, `@`), symbols, emoji |

A **word** is a maximal run of characters that:

1. starts with a letter or digit;
2. continues with letters, digits and marks;
3. may contain a **joiner** only where it is followed by a letter or digit (so one joiner at
   a time, never at the end of a word, never at its start because of rule 1);
4. may contain a **number separator** only where it has a digit immediately before it and a
   digit immediately after it.

Every other character separates words and belongs to none. The words of a text are its
maximal runs in order, left to right; `word_count(text)` is how many there are. Over the
string of class letters (`D` digit, `L` letter, `M` mark, `J` joiner, `S` number separator,
`O` other) the rule is exactly this regular expression, which is how `textkit/counts.py`
implements it:

```
[LD][LDM]*(?:(?:J[LD]|(?<=D)SD)[LDM]*)*
```

`word_count` raises `TypeError` for anything that is not a `str`. The text is not
normalised: composed `"é"` and decomposed `"e"` + U+0301 give the same words because a mark
continues the word it follows.

What this means for the cases the plan asks about:

- **Hyphenated words** are one word (`"well-known"`, `"state-of-the-art"`, `"COVID-19"`).
  A double hyphen, or a hyphen next to a space, separates (`"a--b"` is two words; `"-5"`
  is the word `"5"`). En and em dashes always separate.
- **Apostrophes** inside a word keep it together (`"don't"`, `"rock'n'roll"`, `"O'Neill"`);
  leading and trailing ones are dropped (`"dogs'"` is `"dogs"`, `"'tis"` is `"tis"`), so a
  quoted word is just the word.
- **Numbers** are words. A decimal point or a thousands separator between two digits keeps
  the number whole (`"3.14"`, `"1,000,000"`, `"v1.2.3"`); a `.` or `,` with no digit on one
  side separates (`"1, 2, 3"` is three words, `"e.g."` is two). Currency and percent signs
  are not part of the number (`"$5"` is `"5"`).
- **Other punctuation** always separates, including `_` (`"snake_case"` is two words, as
  the case-conversion helpers will want), `/`, `@` and `+`.
- **Non-ASCII letters** count like ASCII ones, in any script. Scripts written without
  spaces between words (Chinese, Japanese, Thai) are not segmented: a run of their
  characters is one word. Emoji and other symbols separate.

### Examples

Each row is checked by `tests/test_counts.py`, which reads this table: the first column is
a Python string literal, the second the list of words, the third the count.

| Text | Words | Count |
|------|-------|-------|
| `""` | `[]` | 0 |
| `" \t\n "` | `[]` | 0 |
| `"...!?"` | `[]` | 0 |
| `"Hello, world!"` | `["Hello", "world"]` | 2 |
| `"one\ttwo\nthree"` | `["one", "two", "three"]` | 3 |
| `"well-known"` | `["well-known"]` | 1 |
| `"state-of-the-art design"` | `["state-of-the-art", "design"]` | 2 |
| `"a--b"` | `["a", "b"]` | 2 |
| `"-leading and trailing-"` | `["leading", "and", "trailing"]` | 3 |
| `"non‑breaking"` | `["non‑breaking"]` | 1 |
| `"pages 10–20"` | `["pages", "10", "20"]` | 3 |
| `"wait—what"` | `["wait", "what"]` | 2 |
| `"don't"` | `["don't"]` | 1 |
| `"don’t"` | `["don’t"]` | 1 |
| `"rock'n'roll"` | `["rock'n'roll"]` | 1 |
| `"O'Neill"` | `["O'Neill"]` | 1 |
| `"the dogs' bowls"` | `["the", "dogs", "bowls"]` | 3 |
| `"'tis 'quoted'"` | `["tis", "quoted"]` | 2 |
| `"it''s"` | `["it", "s"]` | 2 |
| `"42"` | `["42"]` | 1 |
| `"3.14 and 1,000,000"` | `["3.14", "and", "1,000,000"]` | 3 |
| `"COVID-19 in the 1990s"` | `["COVID-19", "in", "the", "1990s"]` | 4 |
| `"v1.2.3"` | `["v1.2.3"]` | 1 |
| `"-5 degrees"` | `["5", "degrees"]` | 2 |
| `"1, 2, 3"` | `["1", "2", "3"]` | 3 |
| `"1,2,3"` | `["1,2,3"]` | 1 |
| `"e.g. this"` | `["e", "g", "this"]` | 3 |
| `"page 5. Next"` | `["page", "5", "Next"]` | 3 |
| `"$5 or 50%"` | `["5", "or", "50"]` | 3 |
| `"and/or"` | `["and", "or"]` | 2 |
| `"snake_case"` | `["snake", "case"]` | 2 |
| `"me@example.com"` | `["me", "example", "com"]` | 3 |
| `"C++"` | `["C"]` | 1 |
| `"wait...what"` | `["wait", "what"]` | 2 |
| `"hi\U0001f44bthere"` | `["hi", "there"]` | 2 |
| `"Ñandú"` | `["Ñandú"]` | 1 |
| `"naïve café"` | `["naïve", "café"]` | 2 |
| `"café au lait"` | `["café", "au", "lait"]` | 3 |
| `"Привет, мир"` | `["Привет", "мир"]` | 2 |
| `"हिन्दी भाषा"` | `["हिन्दी", "भाषा"]` | 2 |
| `"日本語のテキスト"` | `["日本語のテキスト"]` | 1 |
| `"٢٠٢٦"` | `["٢٠٢٦"]` | 1 |
| `"x² + y²"` | `["x²", "y²"]` | 2 |

## Consequences

- `word_count` gives the counts a reader expects for English prose with contractions,
  compounds and numbers, and works for any script that separates words with spaces.
- The rule is a character classification plus one regular expression, so the shared
  tokenizer (T1.10) can move `_words` from `textkit/counts.py` to `textkit/_tokens.py`
  as is, and the example table above becomes its test as well.
- Known limits, accepted for now: no word segmentation for Chinese, Japanese or Thai;
  `"e.g."` and `"U.S."` count as two words; `"1,2"` in a list without spaces reads as one
  number; a hyphenated line break (`"exam-\nple"`) counts as two words. Changing any of
  these changes `word_count` (and so `reading_time`) and needs a new ADR.
