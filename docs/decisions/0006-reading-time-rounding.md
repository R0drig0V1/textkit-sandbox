<!-- ADR: how textkit.counts.reading_time rounds to whole minutes (plan task T2.1). -->
# 0006. `reading_time` rounds up to whole minutes

## Context

`reading_time(text, wpm=200) -> int` (T2.1) returns whole minutes, computed from
`word_count` (docs/decisions/0002-what-counts-as-a-word.md) divided by `wpm`. The quotient
is rarely whole, so it has to be rounded. The plan asks two questions: what an empty text
gives, and what a text shorter than one minute gives. The options are:

1. **Round down** (floor): a 150-word text at 200 wpm takes `0` minutes, which tells a
   reader a non-empty text takes no time at all.
2. **Round to nearest**: `0` for anything under half a minute, with the same problem, plus
   the tie rule to choose (Python's `round` rounds half to even, so 1.5 and 2.5 both give 2).
3. **Round up** (ceiling): any text with at least one word takes at least `1` minute, and
   only a text with no words takes `0`.
4. **Round up, but at least 1 for every input**, empty included.

The usual use is a "N min read" label, where "0 min" for real content looks broken and
over-estimating by less than a minute is harmless.

## Decision

`reading_time` returns the **ceiling** of `word_count(text) / wpm`, computed in integers
(`-(-words // wpm)`), so it is exact for any word count and never goes through a float:

- **No words** (`""`, whitespace, punctuation only): `0` minutes. A text with nothing to
  read takes no time, and `0` lets callers tell "nothing" apart from "short" (option 4
  would hide that).
- **Under one minute** (1 to `wpm - 1` words): `1` minute.
- **Exact multiples** are not rounded up further: `wpm` words is `1`, `2 * wpm` is `2`.
- Anything in between goes up to the next minute: `wpm + 1` words is `2`.

`wpm` must be an `int` of at least 1: `wpm < 1` raises `ValueError` (the plan), and a
non-`int` (a `float`, a `str`, `None`, or a `bool`, which is technically an `int`) raises
`TypeError`, so every result stays a whole number of minutes by construction. A non-`str`
`text` raises `TypeError` from `word_count`.

## Consequences

- Short texts always show at least one minute; the estimate is never lower than the
  real reading time at the given speed, and is at most one minute higher.
- `reading_time("") == 0` is the only way to get `0`, so callers that want "at least 1"
  for display can write `max(1, reading_time(text))` themselves.
- Fractional speeds (`wpm=237.5`) are not accepted; nobody has asked for them and they would
  bring floats back into the result.
- Changing the rounding later changes results for existing callers and needs a new ADR that
  supersedes this one.

## Cases

| Words (`wpm=200`) | Minutes |
|-------------------|---------|
| 0 | 0 |
| 1 | 1 |
| 199 | 1 |
| 200 | 1 |
| 201 | 2 |
| 400 | 2 |
