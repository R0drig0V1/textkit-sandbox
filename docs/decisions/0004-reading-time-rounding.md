<!-- ADR 0004: how textkit.counts.reading_time rounds to whole minutes (plan task T2.1). -->
# 0004. `reading_time` rounds up to whole minutes

## Context

`textkit.counts.reading_time(text, wpm=200) -> int` (plan task T2.1) returns whole minutes
from `word_count` (whose word rule is ADR 0002), so `word_count(text) / wpm` has to be turned
into an integer. The task asks for a decision on two edge cases: an empty text and a text
that takes less than a minute. The options were:

1. **Round to nearest** (`round(words / wpm)`): 99 words at 200 wpm give `0`, so a short but
   real text claims to take no time, and Python's `round` rounds halves to even
   (`round(0.5) == 0`, `round(1.5) == 2`), which a reader cannot predict.
2. **Round down** (`words // wpm`): every text under one minute gives `0`, the same as an
   empty one.
3. **Round up** (`ceil(words / wpm)`): `0` only when there is nothing to read; anything from
   one word up to `wpm` words gives `1`.
4. **Round to nearest with a floor of 1** for non-empty text: no zero for real text, but two
   rules instead of one, and still the halves question.

## Decision

Option 3, **round up**: `reading_time` returns the smallest whole number of minutes in which
`word_count(text)` words can be read at `wpm` words per minute, computed on integers as
`-(-word_count(text) // wpm)` (no floats, so no floating-point or half-way surprises).

- **Empty text** (and whitespace-only or punctuation-only text, which have no words under
  ADR 0002) gives `0`: there is nothing to read.
- **Under one minute** (1 to `wpm` words) gives `1`: "1 min read" is what readers expect
  for a short text, and a non-zero text never claims to take no time.
- Exactly `n * wpm` words give `n`; one word more gives `n + 1`.

`wpm` must be an `int` of at least 1. `wpm < 1` raises `InvalidValueError` (the plan requires
it; `textkit.errors`, ADR 0006), checked before the text is read, so `reading_time("", 0)`
raises rather than returning `0`. A non-`int` `wpm` (`bool` and `float` included) raises
`TypeError`, which keeps the arithmetic exact; non-`str` `text` raises `TypeError` from
`word_count`.

## Consequences

- The estimate never undercounts: it errs by less than one minute, always upwards. For long
  texts the difference from rounding to nearest is at most one minute.
- `0` means "no words", so callers can test `reading_time(text) == 0` to detect empty text
  without a separate check.
- Callers who want a fractional or differently rounded figure compute it from `word_count`
  themselves; changing the rounding later would change results for most inputs, so it would
  be a breaking change.
- Since the word count comes from ADR 0002, any change to that rule changes reading times.
- `tests/test_counts.py` tests every row below and checks that this table and the tests list
  the same cases.

## Cases

Inputs are Python expressions (string literals, `" ".join(...)` for long texts).

| Input | `wpm` | Minutes |
|-------|-------|---------|
| `""` | 200 | 0 |
| `"   \n\t  "` | 200 | 0 |
| `"!!! ... ---"` | 200 | 0 |
| `"hello"` | 200 | 1 |
| `" ".join(["word"] * 199)` | 200 | 1 |
| `" ".join(["word"] * 200)` | 200 | 1 |
| `" ".join(["word"] * 201)` | 200 | 2 |
| `" ".join(["word"] * 400)` | 200 | 2 |
| `" ".join(["word"] * 401)` | 200 | 3 |
| `"well-known don't 3.14"` | 3 | 1 |
| `"well-known don't 3.14"` | 2 | 2 |
| `"a b c"` | 1 | 3 |
