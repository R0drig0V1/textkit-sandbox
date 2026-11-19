<!-- ADR 0004: how reading_time turns a word count into whole minutes (plan task T2.1). -->
# 0004. Rounding in `reading_time`

- Status: accepted
- Date: 2026-11-18
- Task: T2.1 (`reading_time` in `textkit/counts.py`)

## Context

`reading_time(text, wpm=200) -> int` returns an estimate in **whole minutes**, from
`word_count(text)` (so a word is whatever ADR 0001 says it is) and a reading speed in words
per minute. Dividing words by `wpm` rarely gives a whole number, so the function has to
round, and two cases need a deliberate answer:

- **Empty text** (or text with no words: whitespace, punctuation only). Is that 0 minutes or
  the 1-minute floor that "N min read" labels often show?
- **Under one minute** (say 50 words at 200 wpm). Rounding to the nearest minute gives 0,
  which reads as "nothing to read" for a text that has words in it.

The plan also fixes `wpm < 1` as a `ValueError`; what happens to a `wpm` that is not an
`int` is left to this ADR.

Options considered:

- **Nearest minute** (`round(words / wpm)`). Under one minute becomes 0 for a non-empty
  text, and Python's `round` rounds halves to even (`round(2.5) == 2`), which surprises
  readers of a table like the one below.
- **Floor** (`words // wpm`). Same problem: every text under `wpm` words is 0 minutes.
- **Ceiling, with a minimum of 1 even for empty text**. Saves callers one `if`, but claims
  a minute of reading for nothing at all, and callers can no longer tell "empty" from
  "short".
- **Ceiling** (chosen).

## Decision

`reading_time(text, wpm)` is `ceil(word_count(text) / wpm)`, computed with integer
arithmetic (`-(-words // wpm)`) so it is exact for every count, with no float rounding.
That gives:

- **No words, 0 minutes.** `""`, whitespace only and punctuation only all give 0, because
  `word_count` gives 0 for them (ADR 0001). A caller that wants to hide the label for an
  empty text can test for 0.
- **Under one minute, 1 minute.** Any text with at least one word takes at least one
  minute, so a short text never shows as 0.
- **Otherwise, round up.** Exactly `k * wpm` words give `k` minutes; one word more gives
  `k + 1`. An estimate that errs long is the conventional choice for "N min read" labels.

Arguments are checked before anything is counted:

- `text` that is not a `str` (`bytes` included) raises `TypeError`, as `word_count` does.
- `wpm` that is not an `int` raises `TypeError`. That includes `float` (`250.5` would bring
  back float rounding, and a fractional speed adds nothing to a whole-minute estimate) and
  `bool` (`True` is an `int` in Python, but `wpm=True` is a bug, not a speed of 1).
- `wpm < 1` raises `ValueError` (the plan's rule): 0 would divide by zero and a negative
  speed has no meaning.

## Consequences

- The result is an `int` that is 0 exactly when the text has no words, and never 0 for a
  text that has some.
- Long texts are rounded up by less than a minute, which is noise for an estimate.
- `reading_time` inherits every choice of ADR 0001: `"e.g."` counts as two words, an unspaced
  script run as one. A change to the word rule changes reading times; this ADR does not.
- `reading_time` only calls `word_count`, so the shared tokenizer of T1.10 can change
  `word_count`'s internals without touching this function.
- Callers who need a fractional estimate can compute `word_count(text) / wpm` themselves.

## Cases

Texts are Python string literals; Words is `word_count(text)` and Minutes is
`reading_time(text, wpm)`. `tests/test_counts.py` reads this table and checks every row,
so the table and the code cannot drift apart.

| Text | Words | wpm | Minutes | Case |
|------|-------|-----|---------|------|
| `""` | 0 | 200 | 0 | empty text |
| `" \n\t "` | 0 | 200 | 0 | whitespace only |
| `"... !?"` | 0 | 200 | 0 | punctuation only, no words |
| `""` | 0 | 1 | 0 | empty text at the slowest speed |
| `"Hello"` | 1 | 200 | 1 | one word, under one minute rounds up |
| `"Hello, world!"` | 2 | 200 | 1 | under one minute rounds up |
| `"a b c d"` | 4 | 4 | 1 | exactly one minute |
| `"a b c d e"` | 5 | 4 | 2 | one word over a minute rounds up |
| `"a b c d e f g h"` | 8 | 4 | 2 | exactly two minutes |
| `"a b c d e f"` | 6 | 4 | 2 | a half rounds up, not to even |
| `"a b c"` | 3 | 1 | 3 | slowest allowed speed |
| `"a b c"` | 3 | 1000 | 1 | speed far above the word count |
| `"well-known don't 3.14"` | 3 | 1 | 3 | words counted by the rule of ADR 0001 |
