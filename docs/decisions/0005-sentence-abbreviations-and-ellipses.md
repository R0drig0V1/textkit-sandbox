<!-- ADR: the sentence rule of textkit.counts.sentence_count (plan task T2.2). -->
# 0005. Sentence boundaries: abbreviations and ellipses

## Context

`sentence_count(text) -> int` (plan task T2.2) needs a rule for where a sentence ends.
Counting `.`, `!` and `?` gets three things wrong. Numbers and names split (`"3.14"`,
`"example.com"`). Abbreviations split (`"Dr. Smith"`, `"e.g. an apple"`). And an ellipsis
counts as three sentences, or as one, whether or not the text goes on after it
(`"Wait... what?"` against `"I wonder... Maybe tomorrow."`). Real sentence segmentation
needs language models or long abbreviation dictionaries, which are outside the standard
library. So the rule has to be small, exact and predictable, with its known misses written
down.

## Decision

The text is scanned once, left to right. A sentence ends at an **end mark** that passes the
rules below, and the end of the text closes the last sentence.

1. **End marks.** A run of one or more `.`, `!`, `?` and `…` (U+2026) is one end mark, so
   `"?!"`, `"!!!"` and `"..."` each end at most one sentence.
2. **A space must follow.** An end mark can end a sentence only when whitespace (a space,
   tab or newline) follows it. Closing quotes and brackets (`" ' ” ’ ) ] } »`) may come
   between the mark and the whitespace. So `"3.14"`, `"example.com"` and `"e.g."` inside
   words never split, and `'He said "Stop." Then'` does.
3. **`!` and `?` always end a sentence.** A mark that contains either one, such as `"?..."`,
   ends a sentence whatever comes next.
4. **Abbreviations that never end a sentence.** A single `.` does not end a sentence when
   the token before it, without leading opening quotes or brackets and compared in lower
   case, is one of `mr`, `mrs`, `ms`, `dr`, `prof`, `st` (titles that come before a name)
   or `vs`, `cf`, `e.g`, `i.e` (words that introduce more of the same sentence). So
   `"Dr. Smith"` and `"e.g. Fuji"` stay in one sentence, even before a capital letter.
5. **Ellipses and `etc.` end a sentence unless a lower-case word follows.** An end mark
   made only of dots and `…` with two dots or more (`".."`, `"..."`, `"…"`), or a single
   `.` after `etc`, ends a sentence unless the next word starts with a lower-case letter
   (`str.islower()`). Spaces and opening quotes or brackets before that word are skipped.
   `"Wait... what?"` is one sentence and `"I wonder... Maybe tomorrow."` is two. A word
   that starts with a capital, a digit or a character with no case starts a new sentence.
6. **Every other single `.`** that passes rule 2 ends a sentence.
7. **Only stretches with a word count.** A stretch of text counts as a sentence only if it
   contains at least one alphanumeric character. Under the ADR "What counts as a word",
   that is exactly a stretch with at least one word. So `""` and `"!!! ... ?"` give 0, and
   text with words but no end mark is one sentence. The rule tests `str.isalnum()`
   directly and does not use the word tokenizer, so changes to how words are split do not
   change sentence counts.

## Consequences

- Prose with the common English abbreviations, decimals, domain names, quotes and ellipses
  counts as people expect. Every rule looks at no more than the mark, the token before it
  and the first character of the next word.
- A listed abbreviation that really does end a sentence joins it to the next one:
  `"He lives on Main St. He likes it."` counts 1.
- Abbreviations that are not listed end a sentence when a space follows them, and so do
  initials: `"The U.S. Army won."` and `"J. Smith wrote it."` count 2 each. Initials are left
  out on purpose: `"Plan B. Then"` is as common as `"J. Smith"`, and no rule this small can
  tell them apart.
- A sentence that starts with a lower-case letter right after an ellipsis or `etc.` joins
  the one before it. Sloppy text that starts sentences in lower case after a plain `.` is
  still split, because rule 6 does not look at case.
- A spaced ellipsis (`". . ."`) is three plain periods: `"Wait . . . what"` counts 2. The
  empty stretches between the dots contain no words and add nothing.
- Line breaks are only whitespace: a heading with no end mark joins the first sentence under
  it. Terminators of other scripts (`。`, `！`, `？`, `؟`) are not end marks, and neither is
  an inverted `¿` or `¡` at the start, which is just punctuation inside a sentence.
- Adding an abbreviation, recognising initials or treating blank lines as boundaries
  changes counts, so it needs a new ADR that supersedes this one.

## Cases

`tests/test_counts.py` (`SentenceCountTest`) checks every row (input as a Python literal),
and that this table and its own list of cases are the same.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"Hello world"` | 1 | text with no end mark is one sentence |
| `"Hello. World."` | 2 | a period and a space end a sentence |
| `"Really?! Yes!!!"` | 2 | a run of marks is one end mark |
| `"!!! ... ?"` | 0 | marks with no words are not sentences |
| `"One.  Two.\nThree."` | 3 | any whitespace after the mark, newlines included |
| `"Dr. Smith arrived. He sat down."` | 2 | a title before a name does not end a sentence |
| `"Mr. and Mrs. Smith left."` | 1 | several titles in one sentence |
| `"DR. Who? Prof. X."` | 2 | abbreviations match in any case; `?` always ends one |
| `"Take fruit, e.g. an apple. Or a pear."` | 2 | `e.g.` does not end a sentence |
| `"Fruit, i.e. apples, e.g. Fuji, is sweet."` | 1 | `i.e.` and `e.g.` go on even before a capital |
| `"(e.g. this) works."` | 1 | an opening bracket before the abbreviation is skipped |
| `"Ask the Dr."` | 1 | the end of the text closes the sentence anyway |
| `"Apples, pears, etc. are fruit."` | 1 | `etc.` before a lower-case word goes on |
| `"Apples, pears, etc. Then bread."` | 2 | `etc.` before a capital ends a sentence |
| `"Wait... what?"` | 1 | an ellipsis before a lower-case word goes on |
| `"I wonder... Maybe tomorrow."` | 2 | an ellipsis before a capital ends a sentence |
| `"Wait… what?"` | 1 | U+2026 is an ellipsis too |
| `'He paused... "maybe" not.'` | 1 | an opening quote before the next word is skipped |
| `"Well..."` | 1 | an ellipsis at the end of the text |
| `"What?... No."` | 2 | a mark with `?` always ends a sentence |
| `"Pi is 3.14. It never ends."` | 2 | a dot between digits is not an end mark |
| `"Visit example.com today."` | 1 | a dot with no space after it does not split |
| `'He said "Stop." Then he left.'` | 2 | a closing quote may follow the mark |
| `"(It rained.) We stayed in."` | 2 | a closing bracket may follow the mark |
| `"He lives on Main St. He likes it."` | 1 | known miss: a listed abbreviation never ends one |
| `"The U.S. Army won."` | 2 | known miss: unlisted abbreviations end one |
| `"J. Smith wrote it."` | 2 | known miss: initials are not recognised |
| `"Wait . . . what"` | 2 | a spaced ellipsis is plain periods |
