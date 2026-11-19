<!-- ADR 0004: how textkit.counts.reading_time turns a word count into whole minutes. -->
# 0004. Rounding in `reading_time`

## Context

`reading_time(text, wpm=200)` (plan task T2.1) returns whole minutes, computed from
`word_count` (whose word rule is ADR 0002). A word count divided by a reading speed is
rarely a whole number, so the function needs a rounding rule. The cases people notice are at
the bottom of the scale: an empty text, and a text that takes less than one minute. A
"0 min read" label on a non-empty paragraph looks broken, and "1 min read" on an empty page
claims there is something to read when there is not.

The candidates were:

- **Round down** (`words // wpm`): every text shorter than `wpm` words reads as 0 minutes.
- **Round to nearest**: still gives 0 for anything under half a minute, and needs a
  tie-breaking rule (Python's `round` uses banker's rounding: `round(0.5) == 0`,
  `round(1.5) == 2`).
- **Round to nearest with a floor of 1 for non-empty text**: fixes the bottom of the scale
  but mixes two rules, and still underestimates (1.4 minutes reads as 1).
- **Round up** (ceiling): one rule. It gives 0 only when there are no words, and never
  claims a text is shorter than it is.

## Decision

`reading_time` returns the **ceiling** of `word_count(text) / wpm`:

1. **No words, 0 minutes.** `""`, whitespace-only and punctuation-only text (all 0 words
   under ADR 0002) give 0.
2. **Under one minute, 1 minute.** Any text with at least one word takes at least 1 minute.
3. **Otherwise round up.** Exactly `wpm` words is 1 minute; `wpm + 1` words is 2.
4. **Integer arithmetic.** The ceiling is computed as `-(-words // wpm)`, with no float
   division, so it is exact for any text length.
5. **`wpm < 1` raises `ValueError`**, checked before the text is looked at, so
   `reading_time("", 0)` raises as well.

## Consequences

- The estimate is an upper bound in whole minutes: a reader never runs over it at the
  given speed.
- Short texts are slightly overestimated (1 word reads as 1 minute). This is what reading-time
  labels are for: "at most a minute".
- What counts as a word is not decided here: changing ADR 0002 changes `reading_time` with
  it.
- Changing the rounding needs a new ADR that supersedes this one, and an update of the table
  below and its tests.

## Table of cases

Tested row by row in `tests/test_counts.py` (`ADR_0004_CASES`, same order).

| Input (Python literal) | `wpm` | Minutes | Why |
|------------------------|-------|---------|-----|
| `""` | 200 | 0 | empty text, no words |
| `"!!! ... ?"` | 200 | 0 | punctuation only, no words (ADR 0002) |
| `"word"` | 200 | 1 | under one minute rounds up to 1 |
| `"w " * 199` | 200 | 1 | under one minute rounds up to 1 |
| `"w " * 200` | 200 | 1 | exactly one minute |
| `"w " * 201` | 200 | 2 | one word over rounds up |
| `"w " * 400` | 200 | 2 | exactly two minutes |
| `"w " * 401` | 200 | 3 | one word over rounds up |
| `"one two three"` | 1 | 3 | one word per minute |
| `"well-known don't 3.14"` | 3 | 1 | 3 words under ADR 0002, not more |
