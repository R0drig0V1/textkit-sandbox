<!-- ADR 0005: where sentence_count (T2.2) ends a sentence: abbreviations, ellipses, initials. -->
# 0005. Sentence boundaries: abbreviations and ellipses

- Status: accepted
- Task: T2.2 (`sentence_count` in `textkit/counts.py`)
- Builds on: ADR 0002 (what counts as a word)

## Context

`sentence_count(text) -> int` has to decide where a sentence ends. Splitting on every `.`,
`!` and `?` is the obvious choice, but it breaks on the cases the plan names:

- **Abbreviations.** `"I met Dr. Smith."` and `"Use a list, e.g. this one."` are one sentence
  each, yet both contain a period followed by a space.
- **Ellipses.** `"..."` and `"…"` (U+2026) sometimes end a sentence (`"I waited... Nobody
  came."`) and sometimes only mark a pause inside one (`"Wait... what?"`).

It also has to handle decimals (`"3.14"`), quoted speech (`'"Stop!" he said.'`), text with no
terminator at all, and text with no words. A complete solution needs a language model or a
trained abbreviation list (NLTK's Punkt), neither of which is in the standard library. The
goal is a short rule, predictable enough to write down as a table, that gets ordinary English
prose right and fails in documented ways.

## Decision

### Terminators and boundaries

The **terminators** are `.` U+002E, `!` U+0021, `?` U+003F and `…` U+2026. A maximal run of
them (`"..."`, `"?!"`, `"!!!"`, `".…"`) is one **terminator run**. **Closers** are the
characters `"` `'` `”` `’` `»` `)` `]` `}` that may follow a run before the space
(`'"Stop." Then'`).

A terminator run ends a sentence (is a **boundary**) when all of these hold:

1. **It is followed by whitespace or the end of the text**, after skipping any closers. A
   run glued to the next character is part of the text: `"3.14"`, `"wait...what"`,
   `"end.Next"`, `"example.com"` never split. Newlines are whitespace but are not terminators
   themselves: a title line without a period runs into the next sentence.
2. **The next non-whitespace character is not a lower-case letter** (`str.islower()`). This
   is the ellipsis rule and the general abbreviation rule: `"Wait... what?"`, `"e.g. this"`,
   `"etc. and more"` and `'"Stop!" he said.'` continue; `"Wait... What?"` and
   `"etc. Then"` split. Letters without case (CJK, Devanagari) and digits never continue a
   sentence by this rule.
3. **If the run is a single `.`**, the token before it is neither
   - a **listed abbreviation**, compared after `str.casefold()`: `mr`, `mrs`, `ms`, `mx`, `dr`,
     `prof`, `vs`, `cf`, `e.g`, `i.e` (so `"Dr. Smith"`, `"e.g. Python"`), nor
   - an **initial**: a single character that `str.isupper()` (`"J. R. R. Tolkien"`).

   The token is the text between the previous whitespace and the period, with leading
   non-alphanumerics dropped (`"(Dr"` -> `Dr`). Longer runs (`"Dr.."`, `"Dr.!"`) are
   ellipses or emphasis and get no exception.

The list holds only words that are written with a period and essentially never end a
sentence: titles before a name and the Latin abbreviations that introduce something. `etc`,
`Jr`, `St`, `No` and `a.m`/`p.m` are left out on purpose because they end sentences often
(`"...pears, etc. Then"`); when they do not, rule 2 usually catches it (`"etc. and"`).

### Counting

The boundaries cut the text into pieces. A piece counts as a sentence when it contains at
least one character for which `str.isalnum()` is true, which is the same as containing at
least one word under ADR 0002. So:

- the last piece counts even without a terminator (`"Hello world"` is 1);
- pieces of punctuation or whitespace only are not sentences (`"!!! ... ?"` is 0,
  `"...and then it ended."` is 1);
- `""` and whitespace-only text are 0.

`sentence_count` never raises for any `str`.

### Case table

Every row is tested in `tests/test_counts.py` (`SentenceCountTest`). Inputs are Python string
literals.

| # | Input | Count | Shows |
|---|-------|-------|-------|
| 1 | `""` | 0 | empty text |
| 2 | `" \n\t "` | 0 | whitespace only |
| 3 | `"Hello world"` | 1 | no terminator: the last piece still counts |
| 4 | `"Hello."` | 1 | one sentence |
| 5 | `"Hello. World."` | 2 | period and space |
| 6 | `"Hello.\nWorld."` | 2 | a newline is whitespace after the period |
| 7 | `"Title\n\nBody text."` | 1 | a newline is not a terminator |
| 8 | `"Really?! Yes."` | 2 | a mixed run is one terminator |
| 9 | `"Hi!!!   "` | 1 | trailing run and spaces |
| 10 | `"!!! ... ?"` | 0 | punctuation only |
| 11 | `"I met Dr. Smith. He was kind."` | 2 | listed abbreviation `Dr` |
| 12 | `"Mr. and Mrs. Smith arrived."` | 1 | `Mrs` listed; `Mr.` continues by lower case |
| 13 | `"DR. NO is a film."` | 1 | abbreviations match in any case |
| 14 | `"Use a list, e.g. Python lists."` | 1 | `e.g` listed, followed by a capital |
| 15 | `"Fruit, i.e. apples. Done."` | 2 | `i.e` and lower case |
| 16 | `"Apples, pears, etc. Then we left."` | 2 | `etc` is not listed |
| 17 | `"Apples, pears, etc. and more."` | 1 | lower case continues after an unlisted abbreviation |
| 18 | `"Wait... what?"` | 1 | ellipsis followed by lower case |
| 19 | `"Wait... What?"` | 2 | ellipsis followed by a capital |
| 20 | `"Wait… What?"` | 2 | U+2026 is a terminator |
| 21 | `"wait...what"` | 1 | an ellipsis without a space is no boundary |
| 22 | `"...and then it ended."` | 1 | a leading ellipsis has no words before it |
| 23 | `"Dr.. Smith"` | 2 | the abbreviation rule needs a single period |
| 24 | `"Pi is 3.14. Next."` | 2 | a decimal point is no boundary |
| 25 | `"end.Next"` | 1 | a period without a space is no boundary |
| 26 | `"J. R. R. Tolkien wrote it. He died in 1973."` | 2 | initials |
| 27 | `"I saw plan B. It worked."` | 1 | known error: a capital letter before a period is read as an initial |
| 28 | `"In the U.S. Then we left."` | 2 | `U.S` is not listed |
| 29 | `'He said "Stop." Then he left.'` | 2 | a closing quote after the period |
| 30 | `'"Stop!" he said.'` | 1 | quoted speech followed by lower case |
| 31 | `"(See Dr. Who.) Then more."` | 2 | brackets: leading `(` dropped from the token, `)` is a closer |
| 32 | `"It costs $5. Fine."` | 2 | a number is not an initial |
| 33 | `"¿Qué? ¡Sí!"` | 2 | non-English punctuation before the next sentence |
| 34 | `"Привет. Как дела?"` | 2 | any cased script |
| 35 | `"東京。大阪。"` | 1 | `。` is not a terminator |

## Consequences

- Ordinary English prose with titles, `e.g.`/`i.e.`, initials, decimals, quoted speech and
  ellipses is counted as a reader would count it.
- Known errors, pinned in the table: a sentence ending in a single capital letter merges with
  the next (`"plan B. It"`, row 27); `"the U.S. Army"` is two sentences, the mirror of row 28;
  a missing space after a period merges two sentences (`"end.Next"`, row 25); a sentence
  that starts with a lower-case word merges with the one before it; a title line without a
  period merges with the next line (row 7).
- The abbreviation list is English. Other languages still get rules 1 and 2, which cover
  most of their abbreviations followed by lower case.
- CJK full stops (`。！？`) are not terminators, because they are not followed by spaces and
  rule 1 would need an exception for them; text punctuated only with them counts as one
  sentence (row 35). Adding them is a later, separate decision.
- Changing the terminators, closers, the abbreviation list or the rules changes
  `sentence_count`: it needs a new ADR that supersedes this one and an update of the table
  and its tests.
