<!-- ADR 0004: how reading_time (T2.1) turns a word count into whole minutes. -->
# 0004. `reading_time` rounds up to whole minutes; only a text with no words takes 0

- Status: accepted
- Task: T2.1 (`reading_time` in `textkit/counts.py`)
- Builds on: ADR 0002 (what counts as a word)

## Context

`reading_time(text, wpm=200) -> int` returns whole minutes computed from `word_count(text)`
(the rule of ADR 0002) at `wpm` words per minute. The exact time `words / wpm` is rarely a
whole number, so a rounding rule is needed, and the plan asks it to settle two cases in
particular: an empty text, and a text that takes less than one minute.

The candidates:

1. **Round to nearest** (`round(words / wpm)`). Python's `round` is banker's rounding
   (`round(0.5) == 0`, `round(2.5) == 2`), so the result depends on parity, and every text
   under half a minute (up to 100 words at 200 wpm) reads as 0 minutes: a "0 min read" label
   on a text that has content.
2. **Round down** (`words // wpm`). Every text under one minute (up to 199 words at 200 wpm)
   reads as 0 minutes, and a 399-word text reads as 1.
3. **Round up** (`ceil(words / wpm)`). A text that has any word reads as at least 1 minute;
   an empty text is 0 minutes. The estimate never says a text is shorter than it is.
4. **Round up with a floor of 1**, even for an empty text. Hides the difference between "no
   text" and "a short text", and a caller that wants the floor can write
   `max(1, reading_time(text))`; the reverse (recovering 0 from 1) is impossible.

## Decision

`reading_time` **rounds up**, in integer arithmetic:

```
words   = word_count(text)                 # ADR 0002
minutes = (words + wpm - 1) // wpm         # == ceil(words / wpm) for words >= 0, wpm >= 1
```

- **No words, 0 minutes.** `""`, whitespace only and punctuation only (anything for which
  `word_count` is 0) give `0`. 0 means "nothing to read", not "under a minute".
- **Under one minute, 1 minute.** Any text with 1 to `wpm` words gives `1`.
- **Exact minutes are not rounded up.** `k * wpm` words give `k`; one more word gives
  `k + 1`.
- **Integer arithmetic only**, so there is no floating-point error at the boundaries (with a
  float, `words / wpm` for large counts could land just above or below a whole number).

`wpm` is validated before the text is looked at, so an invalid `wpm` raises even for `""`:

- `wpm < 1` raises `ValueError` (the plan's rule; it applies to any number, `0.5` included).
- Otherwise a `wpm` that is not an `int`, or is a `bool`, raises `TypeError` (`200.0`,
  `True`). Whole-number words per minute keep the integer arithmetic above exact, and
  `True` meaning "1 wpm" is never intended.

### Case table

Every row is tested in `tests/test_counts.py` (`ReadingTimeTest`). Inputs are Python
expressions; `n words` means `" ".join(["word"] * n)`.

| # | Text | `wpm` | Result | Shows |
|---|------|-------|--------|-------|
| 1 | `""` | 200 | 0 | empty text |
| 2 | `" \n\t "` | 200 | 0 | whitespace only has no words |
| 3 | `"!!! ... ?"` | 200 | 0 | punctuation only has no words |
| 4 | `"- " * 500` | 200 | 0 | lone hyphens are not words (ADR 0002) |
| 5 | `"hello"` | 200 | 1 | one word, under one minute |
| 6 | 199 words | 200 | 1 | just under one minute |
| 7 | 200 words | 200 | 1 | exactly one minute is not rounded up |
| 8 | 201 words | 200 | 2 | just over one minute |
| 9 | 400 words | 200 | 2 | exactly two minutes |
| 10 | 401 words | 200 | 3 | just over two minutes |
| 11 | `"well-known " * 201` | 200 | 2 | hyphenated words count once (ADR 0002) |
| 12 | `"one two three"` | 1 | 3 | smallest valid `wpm` |
| 13 | `"one two three"` | 2 | 2 | 1.5 minutes rounds up |
| 14 | `"a b"` | 1000 | 1 | `wpm` far above the word count |
| 15 | `""` | 1 | 0 | empty text with the smallest `wpm` |

Errors:

| Text | `wpm` | Raises |
|------|-------|--------|
| `"hello"` | `0` | `ValueError` |
| `"hello"` | `-5` | `ValueError` |
| `""` | `0` | `ValueError` (checked before the text) |
| `"hello"` | `0.5` | `ValueError` |
| `"hello"` | `200.0` | `TypeError` |
| `"hello"` | `True` | `TypeError` |

## Consequences

- A non-empty text never shows "0 min"; 0 is reserved for texts with no words, so callers can
  test `reading_time(text) == 0` to hide the label.
- Short texts are over-estimated (one word reads as one minute). For a minute-granularity
  label this is the usual convention and errs on the safe side.
- `reading_time` inherits every choice of ADR 0002: `"AT&T"` is two words, CJK runs are one
  word each (so CJK text is under-estimated). A rule change there changes reading times too.
- Fractional `wpm` is not supported; a caller with one can round it first.
