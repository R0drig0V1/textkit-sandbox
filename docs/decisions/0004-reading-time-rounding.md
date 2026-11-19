<!-- 0004-reading-time-rounding: how textkit.counts.reading_time turns a word count into whole minutes. -->
# 0004. Reading time rounds up to whole minutes

## Context

`textkit.counts.reading_time(text, wpm=200)` (plan task T2.1) returns whole minutes, computed
from `word_count` (word rule: [0002-what-counts-as-a-word](0002-what-counts-as-a-word.md)).
Dividing the word count by `wpm` rarely gives a whole number, so the result has to be
rounded, and two cases need an explicit answer: an empty text, and a text that takes less
than one minute. The usual consumer is a "N min read" label.

## Decision

1. `reading_time(text, wpm)` is `ceil(word_count(text) / wpm)`: the word count divided by
   `wpm`, **rounded up** to the next whole minute. Exactly `wpm` words is 1 minute; one word
   more is 2.
2. **Text with no words gives 0.** That covers `""`, whitespace-only and punctuation-only
   text, since it is the word count that matters, not the length of the string.
3. **Any text with at least one word gives at least 1** (a consequence of rule 1): a short
   text reads in "1 min", never "0 min".
4. `wpm` is an `int`. `wpm < 1` raises `ValueError`; a `wpm` that is not an `int`, `bool`
   included, raises `TypeError`, as does a `text` that is not a `str` (from `word_count`).
5. The division is done in integers (`-(-words // wpm)`), so the result is exact for any
   word count, with no floating-point rounding at the boundaries.

Rounding up was chosen over rounding to nearest and over truncation because both of those
give 0 for a short, non-empty text, which reads as "nothing to read" and is wrong; and
because a reader who is told "2 min" and finishes in 1.2 minutes is not misled, while one
told "1 min" for 1.8 minutes is. Keeping 0 for wordless text keeps the function honest
about empty input instead of inventing a minimum the caller cannot tell apart.

## Consequences

- Short texts are overestimated by up to one minute (1 word and 200 words are both 1 minute
  at the default speed). Accepted: the unit is whole minutes.
- A caller who wants "at least 1 min" for empty text, or another rounding, computes it from
  `word_count` directly.
- The result changes whenever the word rule changes; the cases below pin it through
  `word_count`, so a change to that rule that affects them shows up here as well.

## Cases

Inputs are Python string literals; small `wpm` values keep the boundary inputs short.
`tests/test_counts.py` tests every row and checks that this table and its own case list stay
identical.

| Input | wpm | Minutes | Why |
|-------|-----|---------|-----|
| `""` | 200 | 0 | empty text |
| `"   \n\t  "` | 200 | 0 | whitespace only: no words |
| `"!!! ... ?"` | 200 | 0 | punctuation only: no words |
| `"hello"` | 200 | 1 | one word, under one minute, rounds up to 1 |
| `"hello world"` | 200 | 1 | under one minute at the default speed |
| `"one two three"` | 3 | 1 | exactly `wpm` words is 1 minute |
| `"one two three four"` | 3 | 2 | one word over a whole minute rounds up |
| `"one two three four five six"` | 3 | 2 | an exact multiple of `wpm` is not rounded |
| `"one two three four five six seven"` | 3 | 3 | just over two minutes rounds up |
| `"well-known don't"` | 1 | 2 | words counted by the word rule: each joined word is one |
| `"a - b"` | 1 | 2 | a free-standing hyphen is not a word |
| `"hello"` | 1 | 1 | the slowest valid speed |
