<!-- ADR 0004: how textkit.counts.reading_time rounds a word count to whole minutes (T2.1). -->
# 0004. `reading_time` rounds up to whole minutes

## Context

`reading_time(text, wpm=200) -> int` (plan task T2.1, `textkit/counts.py`) turns a word
count into whole minutes. It counts words with `word_count`, so what a word is comes from
ADR 0002 and is not decided again here. The plan leaves the rounding open, and it matters
most at the small end:

- **An empty text**, or one with no words (whitespace, punctuation only): 0 or 1?
- **A text under one minute** (1 to `wpm - 1` words): 0 or 1?
- **The boundary**: what do `wpm` words and `wpm + 1` words give?

Three rules are possible:

1. **Round down** (`words // wpm`). Any short text reads as 0 minutes, so a caller showing
   "0 min read" on a real paragraph needs its own special case. Rejected.
2. **Round to nearest** (`round(words / wpm)`). Python rounds halves to even, so 300 words
   at 200 wpm give 2 but 100 words give 0. Short texts still give 0, and the half-way rule
   surprises readers. Rejected.
3. **Round up** (`ceil(words / wpm)`).

## Decision

Option 3: `reading_time(text, wpm) == ceil(word_count(text) / wpm)`, computed with integer
arithmetic as `-(-words // wpm)`. A float division would lose precision for very large
counts and depend on float rounding; floor division of negated integers is exact.

So:

- a text with **no words** gives **0**: `reading_time("") == 0`, and the same for
  `" \n\t "` and `"!!! ... ?"`, because `word_count` gives 0 for them;
- a text with **at least one word** gives **at least 1**: anything under one minute reads as
  1 minute;
- exactly `wpm` words give 1, `wpm + 1` give 2 (at the default, 200 words is 1 minute and
  201 is 2).

The arguments are checked before any counting:

- `wpm` must be an `int`: `float`, `str`, `None` and `bool` raise `TypeError`. `bool` is a
  subclass of `int`, but `wpm=True` is a bug, not a speed of 1 word per minute.
- `wpm < 1` raises `ValueError`, even for an empty text.
- `text` that is not a `str` raises `TypeError` (from `word_count`). `wpm` is checked first,
  so a call with both arguments wrong raises the `wpm` error.

## Consequences

- 0 means "nothing to read" and never "a short read", so callers can show the value as is
  and still hide it for empty text with `if minutes:`.
- The estimate errs long by less than one minute. That is the usual choice for reading-time
  labels and the safe one for a reader deciding whether they have time.
- A fractional speed (`wpm=250.5`) is not supported. Allowing it later is a widening of the
  accepted types, not a breaking change; this ADR would need a successor.
- A change to the word rule (a successor to ADR 0002) changes `reading_time` too, with no
  change to this rule.
- `tests/test_counts.py` (`ReadingTimeTest`) pins the empty, under-one-minute and boundary
  cases, a custom `wpm`, and the errors.
