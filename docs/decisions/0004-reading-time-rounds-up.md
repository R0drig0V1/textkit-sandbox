<!-- ADR 0004: how reading_time turns a word count into whole minutes. -->
# 0004: `reading_time` rounds up to whole minutes

## Context

`reading_time(text, wpm=200) -> int` (T2.1, `textkit/counts.py`) returns whole minutes,
computed from `word_count` (ADR 0001). Dividing words by words per minute rarely gives a
whole number, so it has to be rounded, and the plan asks for two edge cases to be settled:
an empty text, and a text that takes less than one minute.

The candidates:

- **Round down** (`words // wpm`): any text under `wpm` words, a paragraph or a short
  article, reads as 0 minutes. "0 min read" on real content is wrong for the main use (a
  label next to an article).
- **Round to nearest** (`round(words / wpm)`): still gives 0 for anything under half a
  minute. Python's `round` also uses banker's rounding (`round(0.5) == 0`,
  `round(1.5) == 2`), so the result at exact halves would surprise readers, and the float
  division adds rounding error for very large counts.
- **Round up** (ceiling): a single word gives 1 minute; 0 is only possible when there is
  nothing to read.

## Decision

`reading_time` returns `ceil(word_count(text) / wpm)`, computed with integer arithmetic as
`-(-words // wpm)`.

- **Empty text gives 0.** So do whitespace only and punctuation only, since they have no
  words under ADR 0001. 0 means "nothing to read", which callers can test for, for
  example to hide the label.
- **Under one minute gives 1.** Any text with at least one word takes at least 1 minute.
- **Exact multiples are not rounded up**: 200 words at 200 wpm is 1 minute, 201 is 2.
- `wpm < 1` raises `ValueError` (the plan), even when the text is empty, because the
  argument is invalid whatever the text. A non-`int` `wpm` (`200.0`, `"200"`, `None`, and
  `True`, although `bool` subclasses `int`) raises `TypeError`, and so does a non-`str`
  `text`, the same as `word_count`.

Why integer arithmetic: `words` and `wpm` are both integers, and `-(-a // b)` is the exact
ceiling for `b > 0` at any size, with no float conversion or `math.ceil` call.

## Consequences

- The estimate is never too low, and it can be up to just under a minute too high. That
  matters little at article length and suits a "reading time" label.
- Rounding is applied once to the total. A caller who adds up `reading_time` over several
  sections gets more than `reading_time` of the joined text (every section rounds up
  separately). To get a total, call it on the joined text.
- Anything ADR 0001 decides passes straight through. For example, `"e.g."` counts as two
  words, so text full of such abbreviations reads slightly longer. Changing the word rule
  changes `reading_time` with no change here.
- Only whole minutes and a single speed are supported. Seconds, or different speeds for
  different scripts, would need a new function and a new ADR.

## Cases

`tests/test_counts.py` (`ReadingTimeTest`) asserts every row. "*n* words" means `n` plain
words joined by spaces.

| Text | `wpm` | Minutes | Why |
|------|-------|---------|-----|
| `""` | 200 | 0 | empty text |
| `"  \n\t "` | 200 | 0 | whitespace only: no words |
| `"... !!! ?"` | 200 | 0 | punctuation only: no words |
| `"hello"` | 200 | 1 | under one minute rounds up to 1 |
| 199 words | 200 | 1 | under one minute |
| 200 words | 200 | 1 | an exact multiple is not rounded up |
| 201 words | 200 | 2 | one word over rounds up |
| 400 words | 200 | 2 | exact multiple |
| 401 words | 200 | 3 | rounds up |
| `"one two three"` | 1 | 3 | 1 wpm: minutes equal words |
| `"one two three"` | 2 | 2 | 1.5 rounds up to 2, not banker's rounding |
| any text | 0 or less | `ValueError` | `wpm < 1` |
