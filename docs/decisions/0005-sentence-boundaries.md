<!-- ADR 0005: where sentence_count (T2.2) ends a sentence: abbreviations, ellipses, quotes. -->
# 0005: Sentence boundaries, abbreviations and ellipses

## Context

`sentence_count(text) -> int` (T2.2, `textkit/counts.py`) needs a rule for where a sentence
ends. Splitting on every `.`, `!` and `?` is wrong in common prose:

- **Abbreviations** contain periods that end nothing: `"e.g."`, `"i.e."`, `"Dr. Smith"`,
  `"Mr. and Mrs. Jones"`.
- **Ellipses** (`"..."` or `"…"` U+2026) sometimes end a sentence (`"Wait... Then he
  left."`) and sometimes trail off inside one (`"Wait... what?"`).
- **Numbers and names** carry periods: `"3.14"`, `"v2.0"`, `"example.com"`.
- Terminators come in runs (`"Really?!"`, `"What???"`) and are often followed by a closing
  quote or bracket (`"He said \"Stop.\" Then..."`).

Real sentence segmentation needs language models or large per-language abbreviation lists;
the standard-library-only rule of this package rules both out. So the goal is a small rule
that is predictable, can be reimplemented from this page, and gets ordinary English prose
right, with its known failures written down.

The word rule of ADR 0001 is reused for "has this sentence any content": a stretch of text
with no `str.isalnum()` character (`"..."`, `"!!! ?"`) is not a sentence.

## Decision

Scanning `text` left to right:

1. **Terminators** are `.`, `!`, `?` and `…` (U+2026). A maximal run of them (`"?!"`,
   `"..."`, `"…"`, `"!!!"`) is one **candidate boundary**, so an ellipsis is just a run of
   terminators and gets no rule of its own. Any closing characters right after the run
   (`"`, `'`, `”`, `’`, `)`, `]`, `}`, `»`) belong to it.
2. A candidate **ends the sentence only when it is followed by whitespace or by the end of
   the text** (after its closers). So `"3.14"`, `"v2.0"`, `"example.com"`, the inner period
   of `"e.g."` and `"end.Start"` never end a sentence.
3. **A lowercase letter continues the sentence.** The candidate ends the sentence only if
   the next `str.isalnum()` character after it is not lowercase (`str.islower()` is false:
   upper-case letters, digits and letters of scripts without case all start a new
   sentence). This one rule covers the usual uses of abbreviations and trailing ellipses:
   `"e.g. a hammer"`, `"Wait... what?"`, `"Hey! you there"`.
4. **Titles never end a sentence.** A candidate that is a single `.` right after one of the
   words `Mr`, `Mrs`, `Ms`, `Dr` or `Prof` (exact, case-sensitive match of the run of
   alphanumerics just before the period) does not end the sentence, whatever follows. These
   words come before a name, which starts with a capital, so rule 3 alone would split
   `"Dr. Smith"`. Abbreviations that often end a sentence (`"etc."`, `"Jr."`, `"St."`) are
   left out on purpose.
5. **A sentence must contain a word.** `sentence_count` is the number of stretches between
   boundaries (and the text ends) that contain at least one `str.isalnum()` character. Text
   with words but no terminator is one sentence; `""`, whitespace only and punctuation only
   give 0. Line breaks are whitespace like any other (as in ADR 0003): they never end a
   sentence by themselves.

A non-`str` argument raises `TypeError`, like the other helpers of `textkit.counts`.

Why these choices:

- Rule 2 (whitespace after the terminator) removes every period inside a token at once,
  without needing ADR 0001's digit rule or a list of domain names.
- Rule 3 is the cheapest signal that separates "abbreviation or trailing ellipsis" from
  "sentence end" and needs no word list; it works the same for every cased script.
- Rule 4 is a deliberately tiny, closed list: every entry is a title that is almost never
  the last word of a sentence. A longer list would add as many false merges as it removes
  false splits.

## Consequences

- **False splits** (one sentence counted as two): an abbreviation or an ellipsis followed by
  a capital or a digit, such as `"Use e.g. Python."`, `"The U.S. Army"`, `"approx. 5 km"`,
  `"I went to ... Paris"`. All-caps titles (`"DR. SMITH"`) split too, as rule 4 is
  case-sensitive.
- **False merges** (two sentences counted as one): a sentence that ends in a title
  (`"Ask the Dr. He knows."`), and a new sentence that starts in lower case
  (`"Hello. world"`, `"It works. iPhone users rejoice."`). `"end.Start"` with no space is
  one sentence.
- Headings and list items without a terminator merge with what follows
  (`"Title\n\nBody."` is one sentence); callers who want paragraphs counted separately
  split on blank lines first.
- Only the four terminators above count. Full-width CJK terminators (`。`, `！`, `？`) and
  the interrobang are not terminators, so `"日本語。日本語。"` is one sentence; inverted
  marks (`¿`, `¡`) are ignored and need no handling.
- Changing any rule changes `sentence_count` results; such a change needs a new ADR that
  supersedes this one and an update of the table below and of `tests/test_counts.py`.

## Cases

Inputs are Python string literals. `tests/test_counts.py` (`SentenceCountTest`) asserts
every row.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty (rule 5) |
| `"  \n\t  "` | 0 | whitespace only (rule 5) |
| `"... !!! ?"` | 0 | punctuation only (rule 5) |
| `"Hello"` | 1 | words without a terminator (rule 5) |
| `"Hello."` | 1 | one sentence |
| `"Hello. World."` | 2 | two sentences |
| `"One. Two! Three?"` | 3 | each terminator (rule 1) |
| `"Really?!"` | 1 | a run of terminators is one boundary (rule 1) |
| `"What??? Yes!!!"` | 2 | runs of terminators (rule 1) |
| `"Wait..."` | 1 | an ellipsis at the end |
| `"Wait... what?"` | 1 | an ellipsis before a lowercase letter (rule 3) |
| `"Wait... Then he left."` | 2 | an ellipsis before a capital (rule 3) |
| `"Wait… what?"` | 1 | U+2026 ellipsis before a lowercase letter (rules 1, 3) |
| `"Wait… Then he left."` | 2 | U+2026 ellipsis before a capital (rules 1, 3) |
| `"Use a tool, e.g. a hammer."` | 1 | `"e.g."`: inner period (rule 2), lowercase after (rule 3) |
| `"Use e.g. Python."` | 2 | known false split: abbreviation before a capital |
| `"Dr. Smith is here."` | 1 | title (rule 4) |
| `"Mr. and Mrs. Smith left."` | 1 | lowercase after `"Mr."` (rule 3), title `"Mrs."` (rule 4) |
| `"Prof. Lee met Dr. Who."` | 1 | titles (rule 4) |
| `"Ask the Dr. He knows."` | 1 | known false merge: a sentence ending in a title |
| `"DR. SMITH LEFT."` | 2 | titles are case-sensitive (rule 4) |
| `"Pi is 3.14 today."` | 1 | no whitespace after the period (rule 2) |
| `"Visit example.com now."` | 1 | no whitespace after the period (rule 2) |
| `"end.Start"` | 1 | no whitespace after the period (rule 2) |
| `"He said \"Stop.\" Then he left."` | 2 | a closing quote belongs to the boundary (rule 1) |
| `"(See above.) Next one."` | 2 | a closing bracket belongs to the boundary (rule 1) |
| `"Hello. world"` | 1 | known false merge: lowercase after a period (rule 3) |
| `"Chapter 3. 42 is the answer."` | 2 | a digit starts a sentence (rule 3) |
| `"First line\nSecond line"` | 1 | a line break is not a terminator (rule 5) |
| `"One.\nTwo."` | 2 | a line break is whitespace after a terminator (rule 2) |
| `"... and then it ended. "` | 1 | a leading ellipsis has no word before it (rule 5) |
| `"¿Qué? ¡Sí!"` | 2 | inverted marks are not terminators |
| `"日本語。日本語。"` | 1 | full-width terminators are not terminators |
