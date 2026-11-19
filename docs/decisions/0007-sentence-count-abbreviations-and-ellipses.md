<!-- ADR: the sentence rule of textkit.counts.sentence_count (plan task T2.2). -->
# 0007. Abbreviations and ellipses in `sentence_count`

## Context

`sentence_count(text) -> int` (T2.2) needs a rule for where a sentence ends. Splitting on
every `.`, `!` and `?` over-counts ordinary prose: abbreviations (`"Dr. Smith"`, `"e.g. a
hammer"`), initials (`"J. R. R. Tolkien"`), decimals (`"3.14"`) and ellipses (`"Wait...
what?"`) all contain periods that do not end a sentence. Getting this exactly right needs a
language model or a trained tokenizer; textkit is standard library only and wants a rule that
is small, deterministic and written down case by case.

What counts as a word is already decided in
docs/decisions/0002-what-counts-as-a-word.md; this rule reuses it to decide whether a piece of
text is a sentence at all.

## Decision

A **candidate end** is a run of terminators (`.`, `!`, `?`, `…` U+2026), optionally followed
by closing quotes or brackets (`"`, `'`, `”`, `’`, `»`, `)`, `]`, `}`), and then whitespace or
the end of the text. A terminator followed by anything else ends nothing, so `"3.14"`,
`"e.g.,"` and `"end.Start"` contain no end. A candidate end is a real end as follows:

- **`!` or `?`** in the run: always an end. The run counts once (`"Really?!"`, `"Yes!!!"`).
- **Ellipsis**, a run with `…` or two or more `.` and no `!` or `?`: an end only when the
  next word starts with an upper-case letter (`str.isupper()` on its first letter or digit,
  after skipping whitespace and opening punctuation), or when nothing follows. So
  `"Wait... what? No."` is two sentences and `"I don't know... Maybe tomorrow."` is two.
- **A single `.`**: an end, except after
  - a **known abbreviation**, compared case-insensitively without its final `.`: `Mr`, `Mrs`,
    `Ms`, `Dr`, `Prof`, `Sr`, `Jr`, `St`, `vs`, `etc`, `cf`;
  - **dotted single letters**: one letter, or letters each followed by `.`, such as `e.g.`,
    `i.e.`, `p.m.`, `U.S.` and initials like `J.`.

  The abbreviation is the whitespace-delimited chunk before the `.`, without leading opening
  punctuation, so `"(i.e."` is `i.e`.

The text is cut at every real end. Each piece that contains at least one word (the rule of
docs/decisions/0002-what-counts-as-a-word.md) is a sentence; pieces without words are not, so
`""`, whitespace and punctuation-only text count 0, and trailing text with words but no
terminator counts as a final sentence (`"Hello"` is 1). Line breaks alone do not end
sentences.

## Consequences

- Ordinary prose with titles, Latin abbreviations, initials, decimals and ellipses counts
  as a reader expects.
- An abbreviation or initial that really ends a sentence is not an end: `"Bring pens, paper,
  etc. Then we start."` is one sentence, and so is `"I live in the U.S. It is big."`. The
  list is short on purpose; growing it changes existing counts.
- An ellipsis before a capitalised word that continues the sentence (`"Wait... I think so"`,
  where `I` is upper case) counts as an end, and one before a lower-case word that starts a
  new sentence does not.
- A question or exclamation inside quotes followed by a dialogue tag (`'"Why?" he asked.'`)
  counts as an end.
- Headings or list items without terminators on separate lines merge into one sentence.
- Changing any of these rules changes counts for existing callers and breaks this table: it
  needs a new ADR that supersedes this one.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that this
table and its own list of cases are the same.

| Input | Count |
|-------|-------|
| `""` | 0 |
| `"   \n\t "` | 0 |
| `"..."` | 0 |
| `"!?!"` | 0 |
| `"Hello"` | 1 |
| `"Hello world."` | 1 |
| `"One. Two. Three."` | 3 |
| `"Really?! Yes!!!"` | 2 |
| `"Hi! !!"` | 1 |
| `"Line one\nline two"` | 1 |
| `"Pi is 3.14 exactly. Yes."` | 2 |
| `"Version 2. Next step."` | 2 |
| `"See Dr. Smith. He is in."` | 2 |
| `"Mr. and Mrs. Brown left."` | 1 |
| `"DR. NO. Fine."` | 2 |
| `"Use a tool, e.g. a hammer. Then stop."` | 2 |
| `"Fruit (i.e. apples) is good."` | 1 |
| `"It was 5 p.m. when we met."` | 1 |
| `"J. R. R. Tolkien wrote it."` | 1 |
| `"Bring pens, paper, etc. Then we start."` | 1 |
| `'He said "Stop." Then he left.'` | 2 |
| `"She said “Go.” He went."` | 2 |
| `"Wait... what? No."` | 2 |
| `"I don't know... Maybe tomorrow."` | 2 |
| `"Well… fine."` | 1 |
| `"It ends with an ellipsis..."` | 1 |
