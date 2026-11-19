<!-- ADR 0005: how reading_time rounds to whole minutes and which wpm values it accepts. -->
# 0005. `reading_time` rounds up to whole minutes

Status: accepted (plan task T2.1).

## Context

`reading_time(text, wpm=200) -> int` (T2.1) turns a word count into whole minutes. The words
come from `word_count` (ADR 0001); this function does not tokenize again, so the two can
never disagree on what a word is. `words / wpm` is rarely a whole number, so the function
has to pick a rounding rule, and the rule has to say what happens at the edges:

- an **empty text**, or one with no words (`"..."`, whitespace only);
- a text that takes **under one minute** (1 word at 200 wpm is 0.005 minutes: 0 or 1?);
- **exact multiples** (200 words at 200 wpm) and **halves** (500 words at 200 wpm is 2.5).

It also has to say which `wpm` values are valid.

The candidate rounding modes:

1. **Floor** (`words // wpm`): any text under one minute is 0 minutes, so a 150-word note
   reads as "0 min". It always underestimates.
2. **Round half to even** (Python's built-in `round()`, banker's rounding): `round(2.5)` is
   2 but `round(3.5)` is 4, so 500 words at 200 wpm is 2 minutes and 700 words is 4. The
   halves go in different directions depending on parity, which looks like a bug to anyone
   reading the numbers, and 1-99 words at 200 wpm are 0 minutes.
3. **Round half up** (`floor(x + 0.5)`): consistent at halves, but a short text (under half
   a minute) is still 0 minutes, so "has something to read" and "has nothing to read" look
   the same.
4. **Ceiling** (`ceil(words / wpm)`): 0 only when there are no words, at least 1 for any
   text with a word, exact multiples stay exact, and never an underestimate (by less than
   one minute over). This is also what "N min read" labels usually show.

## Decision

1. **`reading_time` returns `ceil(word_count(text) / wpm)`.** Consequences, in the order
   the plan asks about:
   - a text with no words (empty, whitespace, only punctuation or emoji) is **0** minutes,
     and 0 means exactly that;
   - a text with at least one word is **at least 1** minute, however large `wpm` is;
   - an **exact multiple** is not pushed up: 200 words at 200 wpm is 1, 201 words is 2;
   - a **half** rounds up like every other fraction: 2.5 minutes is 3, 3.5 is 4.
   Python's banker's `round()` is not used anywhere (option 2 above).
2. **The division is exact.** It is done with `fractions.Fraction`, never with float
   division, so `ceil` sees the true quotient: a float that lands a hair above a whole number
   would otherwise add a minute. A `float` `wpm` is read as the decimal `repr()` prints for
   it, which is the number as the caller typed it: `0.3` means 3/10, not its binary value
   0.29999999999999998889..., so 3 words at `0.3` wpm is exactly 10 minutes, not 11.
3. **`wpm` is an `int` or a `float`, greater than zero and finite.** Reading speeds are
   averages and are often computed (`words / minutes`), so a float such as `238.5` is a
   reasonable input and is accepted. Other numeric types (`Decimal`, `Fraction`) are rejected
   with `TypeError`, to keep the accepted set small and documented; convert them first.
   - `wpm <= 0` raises **`ValueError`**: there is no reading speed of zero or less.
   - NaN and infinity raise **`ValueError`**: NaN has no answer, and infinity would make
     every text 0 minutes, contradicting rule 1.
   - `bool` raises **`TypeError`** even though `bool` is an `int` subclass:
     `reading_time(text, True)` is a mistake, not "1 wpm".
   - `wpm` is validated even when the text is empty, so a bad call fails the same way
     whatever the text.
4. **`text` must be a `str`**, `TypeError` otherwise, like `word_count` (`None` and `bytes`
   included; `str` subclasses are fine). `text` is checked before `wpm`, so a call with
   both wrong raises `TypeError` for the text. The error names `reading_time()`, not
   `word_count()`.

## Consequences

- A caller that prints "N min read" never prints "0 min read" for a text with words in it.
- Estimates are an upper bound, off by less than one minute; callers who want floor or
  round-half-up compute it from `word_count(text) / wpm` themselves.
- Any change to the word rule (ADR 0001, or the shared tokenizer of T1.10) changes
  `reading_time` with it, by design.

## Examples

Each row is checked by `tests/test_counts.py`, which reads these tables. The first two
columns are Python expressions: a literal, a string repeated with `* n`, or `float("nan")`
/ `float("inf")`. `"w " * 201` is 201 words.

### Results

| Text | wpm | Minutes |
|------|-----|---------|
| `""` | `200` | 0 |
| `" \t\n "` | `200` | 0 |
| `"... — !? 😀"` | `200` | 0 |
| `"hello"` | `200` | 1 |
| `"hello"` | `1000000000` | 1 |
| `"w " * 199` | `200` | 1 |
| `"w " * 200` | `200` | 1 |
| `"w " * 201` | `200` | 2 |
| `"w " * 300` | `200` | 2 |
| `"w " * 400` | `200` | 2 |
| `"w " * 500` | `200` | 3 |
| `"w " * 700` | `200` | 4 |
| `"well-known don't 3.14"` | `1` | 3 |
| `"w " * 1000` | `1` | 1000 |
| `"w " * 250` | `250.0` | 1 |
| `"w " * 251` | `250.0` | 2 |
| `"w " * 3` | `0.3` | 10 |
| `"w " * 3` | `0.1` | 30 |
| `"w " * 7` | `0.7` | 10 |
| `"w " * 3` | `2.5` | 2 |
| `"w"` | `0.5` | 2 |
| `"w " * 477` | `238.5` | 2 |
| `"w " * 478` | `238.5` | 3 |

The rows of 500 and 700 words at 200 wpm are the halves: `round()` would give 2 and 4. The
rows at `0.3` and `0.7` wpm are the float cases: dividing by the binary values of `0.3`
and `0.7` (both a little under the decimal) would give 11.

### Errors

| Text | wpm | Raises |
|------|-----|--------|
| `"w"` | `0` | `ValueError` |
| `"w"` | `0.0` | `ValueError` |
| `"w"` | `-200` | `ValueError` |
| `"w"` | `-0.5` | `ValueError` |
| `"w"` | `float("nan")` | `ValueError` |
| `"w"` | `float("inf")` | `ValueError` |
| `""` | `0` | `ValueError` |
| `"w"` | `True` | `TypeError` |
| `"w"` | `False` | `TypeError` |
| `"w"` | `"200"` | `TypeError` |
| `"w"` | `None` | `TypeError` |
| `None` | `200` | `TypeError` |
| `b"bytes"` | `200` | `TypeError` |
| `42` | `200` | `TypeError` |
| `None` | `0` | `TypeError` |
