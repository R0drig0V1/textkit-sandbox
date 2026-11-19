<!-- ADR 0004: how textkit.counts.reading_time turns a word count into whole minutes. -->
# 0004. `reading_time` rounds up to whole minutes

## Context

`reading_time(text, wpm=200) -> int` (plan task T2.1) returns whole minutes computed from
`word_count`, whose word rule is ADR 0002. `words / wpm` is rarely a whole number, so the
function has to pick a rounding, and the plan asks two questions in particular: what an
empty text gives, and what a text shorter than one minute gives. The options are:

1. **Floor** (`words // wpm`): any text under `wpm` words reads in 0 minutes, so a
   paragraph would be labelled "0 min read".
2. **Round to nearest** (`round(words / wpm)`): texts under half a minute give 0, and
   Python's `round` uses banker's rounding (`round(2.5) == 2`), so a half-minute goes up or
   down depending on parity. Going through a float also loses exactness for very large
   counts.
3. **Ceiling** (`ceil(words / wpm)`): a partial minute counts as a full one; 0 only when
   there is nothing to read.

## Decision

Ceiling, in integer arithmetic: `reading_time` returns `-(-word_count(text) // wpm)`.

- **Empty text** and any text with no words by ADR 0002 (whitespace, punctuation, emoji)
  give **0**: there is nothing to read.
- **Under one minute**: any text with at least one word gives **at least 1**, whatever
  `wpm` is.
- A partial minute rounds up (201 words at 200 wpm is 2 minutes); an exact multiple does
  not (400 words at 200 wpm is 2).
- `wpm < 1` raises `ValueError` (the plan). `wpm` must be an `int`: a `float` or `bool`
  raises `TypeError`, as does a `text` that is not a `str`.

## Consequences

- The result never under-states the time needed, and 0 means exactly "no words", so a
  caller can test `reading_time(text) == 0` to detect text with nothing to read.
- Short texts are over-stated by up to one minute (one word is "1 minute"). A caller who
  wants finer resolution divides `word_count(text)` by `wpm` itself.
- The result is exact for any word count, with no float rounding.
- `reading_time` inherits the word rule: changing ADR 0002 changes its results too, and the
  rows below that depend on that rule must be reviewed with it.

## Cases

Inputs are Python expressions (a string literal, or a literal repeated with `* N`), called
as `reading_time(text, wpm=wpm)`. `tests/test_counts.py` tests every row and checks that this
table and its own list of cases are the same.

| Input | wpm | Minutes | Why |
|-------|-----|---------|-----|
| `""` | 200 | 0 | empty text: nothing to read |
| `"  \n\t "` | 200 | 0 | whitespace only has no words |
| `"!!! ... 🙂"` | 200 | 0 | punctuation and emoji are not words (ADR 0002) |
| `"hello"` | 200 | 1 | one word: under one minute rounds up to 1 |
| `"word " * 199` | 200 | 1 | just under one minute |
| `"word " * 200` | 200 | 1 | exactly one minute |
| `"word " * 201` | 200 | 2 | a partial minute rounds up |
| `"word " * 400` | 200 | 2 | an exact multiple does not round |
| `"word " * 1000` | 250 | 4 | a custom `wpm` |
| `"one two three"` | 1 | 3 | the slowest allowed `wpm`: one minute per word |
| `"one two three"` | 2 | 2 | 1.5 minutes round up to 2 |
| `"well-known don't 3.14"` | 1 | 3 | words are counted by the rule of ADR 0002 |
| `"hello"` | 1000000 | 1 | any word takes at least one minute |
