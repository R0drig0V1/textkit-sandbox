<!-- ADR 0002-what-counts-as-a-word: the word rule of textkit.counts.word_count (plan task T1.5). -->
# 0002. What counts as a word

## Context

`word_count` (T1.5) needs a definition of "word". Splitting on whitespace (`str.split`)
counts punctuation-only tokens such as `"--"` or `"!"` as words and keeps punctuation glued to
words. Later tasks reuse this rule: T1.10 moves it into a shared tokenizer
(`textkit/_tokens.py`, `words(text)`) that must implement exactly this ADR, and that
`to_snake_case` may adopt where the rules agree. So the rule has to be precise, small and
written down case by case.

The questions the plan asks are hyphenated words, numbers and apostrophes.

## Decision

A **word** is a maximal run of letters and digits (Unicode: `[^\W_]` in a `str` regex, so any
script, and the underscore is *not* a letter). Two runs are joined into one word by a single
**joiner** with a letter or digit immediately on both sides:

- **Hyphen** `-`: `"well-known"`, `"state-of-the-art"` and `"e-mail"` are one word. A hyphen
  with a space on either side, or a double hyphen (`"foo--bar"`, a dash used as punctuation),
  does not join.
- **Apostrophe**, ASCII `'` or typographic `’` (U+2019): `"don't"`, `"O'Brien"`, `"it’s"` are
  one word. A leading or trailing apostrophe is not part of the word: `"'quoted'"` is one word
  and `"dogs'"` is one word, as plain `"dogs"`.
- **Numbers** are words: a run of digits counts like a run of letters (`"42"`, `"2nd"`). A `.`
  or `,` between two digits joins too, so `"3.14"` and `"1,000"` are one word; between letters
  it does not (`"end.Start"` is two words).

Everything else separates words: whitespace of any kind (spaces, tabs, newlines),
punctuation, symbols and `_` (`"already_snake"` is two words). Text with no letters or digits
has no words.

No Unicode normalization is applied. A combining mark (`̈`) is not a letter, so in
decomposed (NFD) text a mark *inside* a word splits it; callers who need otherwise normalize
to NFC first. Precomposed (NFC) text, the usual form, is unaffected.

The rule is one regular expression in `textkit/_tokens.py` (`words`, used by `word_count`):
`[^\W_]+(?:(?:[-'’]|(?<=\d)[.,](?=\d))[^\W_]+)*`.

## Consequences

- Counts match what a reader expects for ordinary prose, including contractions, hyphenated
  compounds and decimal numbers, and punctuation never inflates the count.
- `"already_snake"` and `"snake_case"` are two words each, which is what T1.10 needs to share
  the tokenizer with case conversion; identifiers with `_` are not one word.
- NFD input can over-count; documented here and in the docstring rather than paying for a
  per-character `unicodedata` scan.
- Changing the rule later changes counts for existing callers and breaks this table: it needs a
  new ADR that supersedes this one.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that this
table and its own list of cases are the same.

| Input | Count |
|-------|-------|
| `"well-known"` | 1 |
| `"state-of-the-art design"` | 2 |
| `"a - b"` | 2 |
| `"foo--bar"` | 2 |
| `"42"` | 1 |
| `"3.14"` | 1 |
| `"1,000 people"` | 2 |
| `"2nd place"` | 2 |
| `"don't"` | 1 |
| `"it’s"` | 1 |
| `"'quoted'"` | 1 |
| `"the dogs' bowls"` | 3 |
| `""` | 0 |
| `"!?.,;:--"` | 0 |
| `"   \n\t  "` | 0 |
| `"one  two\n\nthree\tfour"` | 4 |
| `"end.Start"` | 2 |
| `"already_snake"` | 2 |
| `"naïve café"` | 2 |
| `"naïve"` | 2 |
