<!-- ADR: the word rule of textkit.counts.word_count (plan task T1.5), reused by T1.10. -->
# 0001. What counts as a word

## Context

`word_count(text) -> int` (plan task T1.5) needs a rule for what a word is. Splitting on
whitespace (`len(text.split())`) counts `"--"` and `"!!!"` as words and `"Hello,world"` as
one. Splitting on non-alphanumerics counts `"don't"` as two words and `"3.14"` as two numbers.
T1.10 will move the rule into a shared tokenizer (`textkit/_tokens.py`, `words(text)`) and
assert every row of the table below, so the rule has to be exact and the table complete
enough to pin it.

## Decision

A **word** is a maximal run of word characters, where:

1. **Word characters** are the characters for which `str.isalnum()` is true (letters and
   digits of any script), plus combining marks (Unicode category `M*`) that follow one of
   them. So `"naïve"` is one word whether it is typed precomposed (NFC) or decomposed (NFD);
   no normalization is applied.
2. **Hyphens and apostrophes** (`-`, `'` and `’` U+2019) join the two sides into one word
   when there is exactly one of them between two word characters: `"well-known"`,
   `"state-of-the-art"`, `"don't"`, `"it’s"`, `"COVID-19"`. Anywhere else (at either end of
   a word, doubled, or standing alone) they separate and are not part of any word:
   `"'quoted'"` -> `quoted`, `"dogs'"` -> `dogs`, `"a--b"` -> `a`, `b`.
3. **Numbers**: a run of digits is a word, like any other run of word characters. A single
   `.` or `,` between two digits joins them, so `"3.14"` and `"1,000,000"` are one word. A
   sign or a unit is not part of the word: `"-5"` -> `5`, `"$100"` -> `100`, `"50%"` -> `50`.
   Between letters, `.` and `,` separate: `"end.Start"` and `"e.g."` are two words each.
4. **Everything else** (whitespace, other punctuation, symbols, `_`) separates words and is
   never part of one. Runs of separators count as one gap, so leading, trailing and repeated
   spaces or newlines change nothing.

The rule is a single left-to-right scan with one character of lookahead, implemented in
`textkit._tokens.words`; `word_count(text)` is `len(words(text))`.

## Consequences

- Contractions, hyphenated compounds, decimals and thousands separators count as people
  expect in English prose.
- `_` separates, so `"snake_case"` is two words: this is a prose rule, not an identifier
  rule (T1.7 decides identifiers separately; T1.10 reuses this rule there only where they
  agree).
- Scripts written without spaces are one word per run: `"日本語"` counts 1. Proper word
  segmentation for those needs dictionaries outside the standard library.
- Abbreviations with dots count each letter group (`"e.g."` -> 2), and `/` and `:` separate
  numbers (`"1/2"` and `"10:30"` -> 2). Changing any of these later changes counts, so it
  needs a new ADR that supersedes this one.
- A spaced dash is not a word (`"a -- b"` -> 2), but a hyphen-minus used as a dash without
  spaces joins (`"yes-no"` -> 1): the rule cannot tell a hyphen from an unspaced dash.

## Cases

`tests/test_counts.py` checks every row (input as a Python literal), and that this table and
its own list of cases are the same.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"hello"` | 1 | one plain word |
| `"Hello, world!"` | 2 | punctuation next to words separates them |
| `"!!! ... ?"` | 0 | punctuation only |
| `"  one \n\n two\t three  "` | 3 | runs of spaces, tabs and newlines are one gap |
| `"well-known"` | 1 | hyphenated word |
| `"state-of-the-art design"` | 2 | several hyphens, each between word characters |
| `"a -- b"` | 2 | a spaced dash is not a word |
| `"a--b"` | 2 | a doubled hyphen separates |
| `"-leading trailing-"` | 2 | hyphens at the ends are dropped |
| `"don't"` | 1 | word with an apostrophe |
| `"it’s"` | 1 | typographic apostrophe (U+2019) |
| `"'quoted'"` | 1 | apostrophes used as quotes are dropped |
| `"the dogs' bones"` | 3 | trailing possessive apostrophe is dropped |
| `"42"` | 1 | a number |
| `"3.14"` | 1 | decimal point between digits joins |
| `"1,000,000"` | 1 | thousands separators between digits join |
| `"-5"` | 1 | a sign is not part of the number |
| `"COVID-19"` | 1 | hyphen between a letter and a digit joins |
| `"end.Start"` | 2 | a dot between letters separates |
| `"e.g."` | 2 | abbreviations count each letter group |
| `"1/2"` | 2 | a slash separates numbers |
| `"snake_case"` | 2 | an underscore separates |
| `"naïve café"` | 2 | non-ASCII letters are word characters |
| `"naïve"` | 1 | a combining mark (NFD) continues the word |
| `"日本語"` | 1 | a script without spaces is one run |
