<!-- ADR 0005: what ends a sentence for sentence_count (plan task T2.2). -->
# 0005. Sentence ends: abbreviations and ellipses

- Status: accepted
- Task: T2.2 (`sentence_count` in `textkit/counts.py`)

## Context

`sentence_count(text) -> int` has to decide where a sentence ends. Splitting at every `.`,
`!` and `?` is wrong for ordinary prose:

- **Abbreviations** end in a dot without ending the sentence: `"e.g. a hammer"`,
  `"Dr. Smith"`. Some of them also end sentences (`"... and so on, etc."`), so no rule
  that only looks at the abbreviation can be right every time.
- **Ellipses** (`"..."`, or the single character `…` U+2026) sometimes end a sentence
  (`"Wait... What?"`) and sometimes only mark a pause (`"Wait... what?"`).
- **Dots inside tokens** are not ends at all: `"3.14"`, `"v1.2"`, `"example.com"`, and the
  first dot of `"e.g."`.
- **Runs** such as `"?!"`, `"!!!"` and `"..."` are one end, not several.

Options considered for abbreviations:

1. **A long abbreviation dictionary** (as in NLTK's Punkt or ICU). Accurate for one language,
   but it is a dataset to maintain, is English-only, and still cannot tell a final `"etc."`
   from a medial one.
2. **Look at what follows**: a dot followed by a lower-case letter does not end the sentence,
   since sentences start with a capital in the languages textkit counts words for. This
   handles `"e.g."`, `"i.e."`, `"etc."`, `"approx."` and ellipses in one rule, with no list.
   It fails on abbreviations that are normally followed by a capital: titles before a name.
3. **Option 2 plus a short list** of abbreviations that are (almost) never the last word of
   a sentence, for exactly the case option 2 misses.

Option 3 is chosen. It needs only the standard library and stays explainable in one
paragraph; the list is kept short so that it does not turn into option 1.

## Decision

A **sentence** is a stretch of text that contains at least one *word character* and ends at
a *sentence end* or at the end of the text. Word characters are those of ADR 0001 (Unicode
categories `L*`, `N*` and `M*`). So:

- Text with words but no terminator is one sentence (`"hello world"` is 1).
- `""`, whitespace only and punctuation only are 0 sentences; a terminator with no word
  before it (`"?!"`, `"!!! ... ?"`) closes nothing.

A **terminator run** is a maximal run of the characters `.`, `!`, `?` and `…` (U+2026). A run
is a **sentence end** when all of these hold:

1. **It is not glued to the next token.** After the run and any closing quotes or brackets
   (`"`, `'`, `”`, `’`, `)`, `]`, `}`, `»`) comes whitespace or the end of the text. So
   `"3.14"`, `"example.com"` and `"Hi.Bye."` do not split there.
2. **A run containing `!` or `?` always ends the sentence**, whatever follows
   (`"Really? yes."` is 2). These marks are not used in abbreviations, so there is nothing
   to guess.
3. **A run of only `.` and `…` ends the sentence unless one of the two exceptions applies:**
   - **Lower-case continuation:** the next non-whitespace character is a lower-case letter
     (`str.islower()`). This is the rule for abbreviations (`"e.g. a hammer"`,
     `"etc. and more"`) and for ellipses used as a pause (`"Wait... what?"`), and it also
     keeps `"'Done.' she said."` as one sentence.
   - **Non-final abbreviation:** the run is a single `.` and the word characters right
     before it are exactly one of `Dr`, `Mr`, `Mrs`, `Ms`, `Prof`, `vs` (case-sensitive).
     These are followed by a name or a capitalised word, so the lower-case rule cannot
     catch them.

`sentence_count` raises `TypeError` for anything that is not a `str`, like `word_count`.

## Consequences

- An abbreviation followed by a capital, and not on the list, ends a sentence:
  `"e.g. Paris is big."` is 2. Getting it right needs a dictionary and still guesses.
- A sentence that starts with a lower-case letter after a dot or an ellipsis is merged into
  the previous one (`"I said... no."` is 1); so is text with no capitals at all.
- A title at the real end of a sentence is missed (`"I called the Dr. He came."` is 1).
  The list leaves out `St`, `Jr`, `Sr` and `etc` for this reason: they often end sentences.
- Terminators of scripts without spaces (`。`, `！`, `？`, full-width forms) are not
  recognised, and those scripts do not put whitespace after them anyway: `"日本語。日本語。"` is
  1, consistent with ADR 0001 not segmenting them.
- A terminator not followed by whitespace never ends a sentence, so a missing space after a
  full stop (`"Hi.Bye."`) merges two sentences. This is the price of not splitting numbers,
  versions, domains and file names.
- Adding an abbreviation to the list, or another terminator, is a change to this ADR and to
  its case table.

## Cases

Inputs are Python string literals. `tests/test_counts.py` checks every row, and checks that
this table and its own list of cases are the same.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"   \n\t "` | 0 | whitespace only |
| `"!!! ... ?"` | 0 | punctuation only |
| `"?!"` | 0 | a terminator run with no word before it |
| `"hello world"` | 1 | no terminator: one sentence |
| `"Hello world."` | 1 | one sentence with its full stop |
| `"Hi. Bye."` | 2 | two sentences |
| `"Hello.\nWorld"` | 2 | a newline is whitespace; the last sentence has no terminator |
| `"Is it?! Yes."` | 2 | `?!` is one terminator run |
| `"Wait!!! Stop."` | 2 | `!!!` is one terminator run |
| `"Really? yes."` | 2 | `?` ends a sentence even before a lower-case letter |
| `"Pi is 3.14 today."` | 1 | a decimal point is glued to its digits |
| `"See example.com now."` | 1 | a dot inside a token |
| `"Hi.Bye."` | 1 | no whitespace after the dot: not an end |
| `"e.g."` | 1 | an abbreviation on its own |
| `"Use a tool, e.g. a hammer."` | 1 | abbreviation followed by a lower-case letter |
| `"e.g. Paris is big."` | 2 | limitation: abbreviation not on the list, before a capital |
| `"I saw Dr. Smith. He waved."` | 2 | `Dr.` is a non-final abbreviation |
| `"Mr. Lee met Ms. Ada."` | 1 | `Mr.` and `Ms.` are non-final abbreviations |
| `"Wait... what?"` | 1 | ellipsis followed by a lower-case letter |
| `"Wait... What?"` | 2 | ellipsis followed by a capital ends the sentence |
| `"Wait… What?"` | 2 | the ellipsis character U+2026 |
| `"And so…"` | 1 | an ellipsis at the end of the text |
| `"He said 'Stop.' Then he left."` | 2 | closing quote between the full stop and the space |
| `"'Done.' she said."` | 1 | closing quote, then a lower-case letter |
| `"(Really?) Yes."` | 2 | closing bracket after the question mark |
| `"¿Qué? Sí."` | 2 | non-ASCII letters; `¿` is not a terminator |
| `"日本語。日本語。"` | 1 | `。` is not a terminator |
