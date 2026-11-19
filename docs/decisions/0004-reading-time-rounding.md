<!-- ADR: how textkit.counts.reading_time rounds minutes (plan task T2.1). -->
# 0004. Reading time rounding

## Context

`reading_time(text, wpm=200) -> int` (plan task T2.1) returns whole minutes from
`word_count` (ADR 0001, "What counts as a word"). `words / wpm` is rarely a whole number,
so the function needs a rounding rule, and the plan asks in particular what an empty text
and a text that takes under one minute give. The usual choices:

- **Round down** (`words // wpm`): any text under `wpm` words is a 0-minute read, which
  reads as "nothing to read" for a real paragraph.
- **Round to nearest** (`round(words / wpm)`): still 0 for anything under half a minute, and
  Python's `round` uses banker's rounding (`round(0.5) == 0`, `round(1.5) == 2`), which is
  surprising in a count shown to people.
- **Round up** (`ceil(words / wpm)`): never under-promises; the common "N min read"
  convention.

## Decision

`reading_time` returns `ceil(word_count(text) / wpm)`, computed with integer arithmetic
(`-(-words // wpm)`) so that it is exact for any word count:

1. **No words gives 0.** `""`, whitespace-only and punctuation-only text have 0 words and
   take 0 minutes. No floor of 1 is added: "0 min" is the honest answer for nothing to read,
   and callers that want to hide it can test for 0.
2. **Under one minute gives 1.** Any text with at least one word takes at least 1 minute.
3. **Partial minutes round up**: 201 words at 200 wpm is 2 minutes; exactly 200 is 1.
4. **`wpm` must be an `int` of at least 1**: `wpm < 1` raises `ValueError`; a non-`int`
   (including `float` and `bool`) raises `TypeError`, so the result stays an exact integer
   computation. `wpm` is checked before the text is counted, so `reading_time("", 0)` raises.

## Consequences

- Short texts always show "1 min", never "0 min", which matches what readers expect from
  the label.
- Estimates lean high by up to one minute; for long texts that is negligible.
- A fractional reading speed (`wpm=237.5`) is not accepted; callers round it themselves.
- The count inherits every choice of ADR 0001 (`"e.g."` is 2 words, `"日本語"` is 1), so a
  change to the word rule changes reading times too.

## Cases

`tests/test_counts.py` (`ReadingTimeTest.test_adr_table`) checks every row, with a text of
that many words.

| Words | wpm | Minutes | Why |
|-------|-----|---------|-----|
| 0 | 200 | 0 | no words, nothing to read |
| 1 | 200 | 1 | under one minute rounds up to 1 |
| 199 | 200 | 1 | under one minute rounds up to 1 |
| 200 | 200 | 1 | exactly one minute |
| 201 | 200 | 2 | a partial minute rounds up |
| 400 | 200 | 2 | exactly two minutes |
| 401 | 200 | 3 | a partial minute rounds up |
| 5 | 1 | 5 | the smallest valid `wpm` |
