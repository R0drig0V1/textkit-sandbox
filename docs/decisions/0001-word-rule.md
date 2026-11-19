<!-- ADR 0001: the word rule behind word_count (plan task T1.5) and every helper built on it. -->
# 0001. What counts as a word

## Context

`word_count` (plan task T1.5) needs a definition of "word". Later tasks build on the same
rule: `reading_time` (T2.1) counts words through `word_count`, `sentence_count` (T2.2) lives
next to it, and the shared tokenizer `textkit/_tokens.words` (T1.10) must implement this rule
*exactly* and assert one row of the table below per case. So the rule has to settle the
questions people disagree on (hyphens, apostrophes, numbers, punctuation, non-Latin text) and
has to be precise enough that two people would write the same tokenizer from it.

Options considered:

- **`len(text.split())`** (whitespace tokens). Simple, but `"Hello , world !"` counts 4 and
  `"..."` counts 1: punctuation becomes words.
- **`re.findall(r"\w+", text)`**. Counts `_` as a letter (`"foo_bar"` is one word) and splits
  `"don't"`, `"well-known"` and `"3.14"` into two each.
- **A letters-and-digits run with joiners** (chosen). Close to what a reader counts, needs no
  dependency and no locale, and is defined in terms of `str` methods every Python has.

## Decision

Classify every character of `text` (code points, no normalization):

- **letter or digit**: `char.isalnum()` is true. Any script counts, so do digits and other
  numeric characters (`"½"`). `_` is *not* one.
- **mark**: `unicodedata.category(char)` starts with `M` (combining accents, vowel signs).
- **joiner**: `-` (U+002D), `'` (U+0027) or `’` (U+2019).
- **number joiner**: `.` or `,`.
- **separator**: everything else (whitespace, other punctuation, `_`, symbols, emoji).

A **word** is a maximal run that:

1. starts with a letter or digit;
2. continues over letters, digits and marks;
3. continues over **one** joiner when the character right after it is a letter or digit;
4. continues over **one** number joiner when the last letter or digit before it and the
   character right after it are both decimal digits (`str.isdecimal()`);
5. ends at any other character, which belongs to no word.

`word_count(text)` is the number of words. Anything that is not a `str` (`bytes` included)
raises `TypeError`; `words` (T1.10) behaves the same.

Consequences of the rule, by question:

- **Hyphenated words** are one word (`"state-of-the-art"`). A doubled hyphen used as a dash
  splits (`"well--known"` is two); a hyphen at either end is dropped (`"-5"` is `"5"`).
- **Apostrophes** inside a word keep it whole (`"don't"`, `"rock'n'roll"`, both the ASCII and
  the typographic apostrophe). A trailing or leading apostrophe or quote is dropped
  (`"students'"` is `"students"`).
- **Numbers** are words. Decimal points and thousands separators keep a number whole
  (`"3.14"`, `"1,000,000"`, `"v1.2.3"`); signs, `%`, currency symbols and a final `.` are not
  part of it.
- **Dotted abbreviations** split: `"e.g."` is two words and `"U.S.A."` three, because `.`
  joins digits only. Telling abbreviations from sentence ends is T2.2's problem, not this
  rule's.
- **Identifiers**: `_` separates (`"foo_bar"` is two words), case changes do not
  (`"camelCase"` is one). T1.10 must keep these rows when `to_snake_case` reuses `words`.
- **Accents** count as part of the word in both NFC and NFD form; a mark with no word before
  it is dropped.
- **Scripts without spaces** (Chinese, Japanese, Thai): each unbroken run is one word. Proper
  segmentation needs dictionaries outside the standard library; out of scope.

## Consequences

- `word_count` is linear, standard library only and independent of locale and Python
  version (the `str` methods it uses exist on 3.9).
- The table below is the contract. `tests/test_counts.py` reads it from this file and checks
  every row against `word_count`, so the table and the code cannot drift apart silently;
  T1.10 asserts the same rows (the Words column) against `words`. Changing the rule means
  changing this ADR, its table and the tests in one PR.
- Known divergences from a human count: dotted abbreviations, unspaced scripts, and `C++` /
  `C#` (counted as `C`).

## Cases

Inputs and words are Python string literals; Count is `word_count(input)`.

| Input | Count | Words | Case |
|-------|-------|-------|------|
| `""` | 0 | `[]` | empty text |
| `"   "` | 0 | `[]` | spaces only |
| `"\n\n"` | 0 | `[]` | newlines only |
| `"a  b\n\nc\td"` | 4 | `["a", "b", "c", "d"]` | several spaces, newlines and a tab |
| `"Hello, world!"` | 2 | `["Hello", "world"]` | punctuation next to words |
| `"..."` | 0 | `[]` | punctuation only |
| `"!?, -- ;"` | 0 | `[]` | punctuation and dashes only |
| `"well-known"` | 1 | `["well-known"]` | hyphenated word |
| `"state-of-the-art"` | 1 | `["state-of-the-art"]` | several hyphens |
| `"well--known"` | 2 | `["well", "known"]` | doubled hyphen splits |
| `"- dash -"` | 1 | `["dash"]` | hyphens at the ends are dropped |
| `"don't"` | 1 | `["don't"]` | ASCII apostrophe |
| `"don’t"` | 1 | `["don’t"]` | typographic apostrophe |
| `"rock'n'roll"` | 1 | `["rock'n'roll"]` | several apostrophes |
| `"students' books"` | 2 | `["students", "books"]` | trailing apostrophe is dropped |
| `"'quoted'"` | 1 | `["quoted"]` | single quotes around a word |
| `"42"` | 1 | `["42"]` | number |
| `"3.14"` | 1 | `["3.14"]` | decimal number |
| `"1,000,000"` | 1 | `["1,000,000"]` | thousands separators |
| `"v1.2.3"` | 1 | `["v1.2.3"]` | version number |
| `"-5 degrees"` | 2 | `["5", "degrees"]` | sign is not part of the number |
| `"50% off"` | 2 | `["50", "off"]` | percent sign separates |
| `"1.5."` | 1 | `["1.5"]` | final dot is dropped |
| `"e.g."` | 2 | `["e", "g"]` | dotted abbreviation splits |
| `"end.Start"` | 2 | `["end", "Start"]` | dot between letters splits |
| `"foo_bar"` | 2 | `["foo", "bar"]` | underscore separates |
| `"camelCase"` | 1 | `["camelCase"]` | case change does not split |
| `"C++ and C#"` | 3 | `["C", "and", "C"]` | symbols separate |
| `"café"` | 1 | `["café"]` | accent, NFC |
| `"café"` | 1 | `["café"]` | accent, NFD (combining mark) |
| `"́abc"` | 1 | `["abc"]` | leading combining mark is dropped |
| `"Привет, мир"` | 2 | `["Привет", "мир"]` | Cyrillic |
| `"日本語"` | 1 | `["日本語"]` | unspaced script is one run |
| `"\U0001f642 ok"` | 1 | `["ok"]` | emoji separates |
