<!-- ADR 0004: how reading_time (T2.1) turns a word count into whole minutes. -->
# 0004. Reading time rounds up to whole minutes

- Status: accepted
- Task: T2.1 (`reading_time` in `textkit/counts.py`)

## Context

`reading_time(text, wpm=200) -> int` returns whole minutes computed from
`word_count(text)` (ADR 0001) and a reading speed in words per minute. Dividing words by
`wpm` rarely gives a whole number, so the result has to be rounded, and two edge cases need
an explicit answer:

- **An empty text** (no words: `""`, whitespace only, punctuation only).
- **A text under one minute** (between 1 and `wpm - 1` words).

The options considered:

- **Round down** (`words // wpm`): any short text reads as 0 minutes, which tells a reader
  that a paragraph takes no time at all, and a 399-word text at 200 wpm is "1 minute".
- **Round to nearest** (`round(words / wpm)`): Python rounds halves to even, so 300 and 500
  words at 200 wpm give 2 and 2; texts under half a minute still read as 0 minutes; and it
  goes through a float.
- **Round up** (`ceil(words / wpm)`): 0 words is exactly 0 minutes, anything else is at
  least 1 minute, and the estimate never understates the time needed. This is what
  "N min read" labels on publishing sites usually show.

## Decision

`reading_time` returns `ceil(word_count(text) / wpm)`, computed with integers as
`-(-word_count(text) // wpm)`.

- **Empty text**: a text with no words (as counted by ADR 0001) takes **0** minutes. This
  includes whitespace-only and punctuation-only text.
- **Under one minute**: any text with at least one word takes **at least 1** minute.
- **Partial minutes round up**: 201 words at 200 wpm is 2 minutes; exactly 200 words is 1.
- **Validation**: `wpm < 1` raises `ValueError` (the plan). `wpm` that is not an `int`
  (a `float`, a `str`, or a `bool`, although `bool` subclasses `int`) raises `TypeError`, and
  so does a `text` that is not a `str` (through `word_count`). `wpm` is checked before the
  text is counted.

## Consequences

- The estimate errs on the long side by less than one minute; it is never 0 for a text a
  reader has to read.
- Integer arithmetic only: no float rounding surprises, and the result is exact for any size.
- Fractional speeds (`wpm=250.5`) are not accepted; callers round their speed first. Allowing
  floats later is a backwards-compatible change to this ADR.
- The result follows ADR 0001's word rule, so a change to that rule changes reading times.

## Cases

`tests/test_counts.py` checks every row with a text of exactly *Words* words, and checks
that this table and its own list of cases are the same.

| Words | wpm | Minutes | Why |
|-------|-----|---------|-----|
| 0 | 200 | 0 | empty text |
| 0 | 1 | 0 | empty text at the smallest speed |
| 1 | 200 | 1 | under one minute rounds up to 1 |
| 199 | 200 | 1 | just under one minute |
| 200 | 200 | 1 | exactly one minute |
| 201 | 200 | 2 | a partial minute rounds up |
| 400 | 200 | 2 | exactly two minutes |
| 401 | 200 | 3 | a partial third minute rounds up |
| 5 | 1 | 5 | smallest speed: one word per minute |
| 1 | 1000 | 1 | a very high speed still gives 1 minute |
