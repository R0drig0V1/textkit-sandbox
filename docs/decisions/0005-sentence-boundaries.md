<!-- ADR 0005: where a sentence ends for sentence_count (plan task T2.2): abbreviations and ellipses. -->
# 0005. Where a sentence ends: abbreviations and ellipses

## Context

`sentence_count(text)` (plan task T2.2) counts sentences. The naive rule, "split on `.`,
`!` and `?`", is wrong for text people actually write:

- **Abbreviations** end in a dot that does not end the sentence: `"Dr. Smith is here."` and
  `"Use e.g. apples."` are one sentence each.
- **Ellipses** (`...` or `…`) can trail off at the end of a sentence (`"I see... Let us go."`,
  two) or pause inside one (`"Wait... what?"`, one).
- **Dots inside tokens**: `"3.14"`, `"example.com"`, `"v1.2.3"`.
- **Runs of terminators** (`"Really?!"`, `"Wait!!!"`) and **closing quotes and brackets**
  after them (`"“Help!” he cried."`).

ADR 0001 decides what a word is and leaves this problem to T2.2 explicitly ("Telling
abbreviations from sentence ends is T2.2's problem"). Telling them apart perfectly needs a
trained model or a per-language dictionary, both outside the standard library. The rule
below has to be small, independent of locale and precise enough to test row by row.

Options considered:

- **Split on every terminator** (`re.split(r"[.!?]+", text)`). Splits `"3.14"`, `"e.g."`,
  `"Dr."` and every ellipsis: wrong on the most common cases.
- **A long abbreviation list** (`Mr.`, `etc.`, `approx.`, `Jan.`, `No.` ...). Never complete,
  English only, and many entries (`etc.`, `No.`) end sentences as often as not.
- **Capitalization heuristic only**: a terminator followed by space ends a sentence unless the
  next word starts with a lower-case letter. Handles `"e.g. apples"`, `"Wait... what?"` and
  `"“Help!” he cried."` with no list, but fails titles, which are always followed by a
  capitalized name (`"Dr. Smith"`).
- **Capitalization heuristic plus a short list** of abbreviations that are (almost) never the
  last word of a sentence (chosen). The list stays short because it only needs the words the
  heuristic gets wrong: titles before names, and Latin abbreviations that introduce more text.

## Decision

**Terminators** are `.`, `!`, `?`, `…` (U+2026) and the full-width `。`, `！`, `？`. A
**terminator run** is a maximal sequence of consecutive terminators (`"?!"`, `"..."`,
`"!!!"`); it acts as one terminator. **Closers** are `"`, `'`, `”`, `’`, `»`, `›`, `)`, `]`
and `}`; any number of them directly after a run belong to the sentence the run ends.

A terminator run ends a sentence (a **boundary** right after its closers) when:

1. the run contains a full-width terminator (`。`, `！`, `？`): always, because the scripts
   that use them put no space between sentences (`"你好。再见。"` is two); otherwise,
2. the run, with its closers, is followed by whitespace (any `str.isspace()` character,
   newlines included), and
3. the first letter or digit (`str.isalnum()`) after that whitespace is not a lower-case
   letter (`str.islower()` is false), and
4. the run is not a single `.` that ends one of the **abbreviations** `Mr.`, `Mrs.`, `Ms.`,
   `Dr.`, `Prof.`, `e.g.`, `i.e.`, `cf.` or `vs.`. The candidate is the run of
   non-whitespace characters that ends at the dot, with leading characters that are not
   letters or digits removed (so `"(i.e."` is `"i.e."`), compared with `str.casefold()`
   (so `"DR."` matches).

A run followed by anything else (a letter, a digit, other punctuation) is not a boundary:
`"3.14"`, `"example.com"` and `"Hello.World."` stay one sentence. The end of the text is
always a boundary.

The boundaries cut the text into pieces. A **sentence** is a piece that contains at least one
word by ADR 0001 (`textkit._tokens.words`), so text without a final terminator still counts
(`"Hello"` is one sentence) and pieces of punctuation only do not (`"..."` is zero).
`sentence_count(text)` is the number of sentences. Anything that is not a `str` (`bytes`
included) raises `TypeError`, as `word_count` does.

Consequences of the rule, by question:

- **Abbreviations followed by a lower-case word** never split, listed or not: `"etc. are"`,
  `"The U.S.A. is big."`. Followed by a capital, only the listed ones hold: `"Dr. Smith"`
  and `"e.g. Paris"` stay one sentence, `"etc. Then"` and `"the U.S.A. It is"` split, which is
  usually right because those abbreviations often end a sentence.
- **Ellipses** follow the same rule as a dot: `"Wait... what?"` is one sentence,
  `"I see... Let us go."` two, a trailing `"And then..."` one, a leading `"...and then"` one.
  `...` and `…` behave the same; an ellipsis is never an abbreviation.
- **`!` and `?`** follow the same capitalization rule, so a quoted exclamation with a speech
  tag stays one sentence (`"“Help!” he cried."`), and so does casual `"what? yes."`.
- **Newlines** are whitespace and nothing more: a line without a terminator runs into the
  next one (`"Line one\nLine two"` is one sentence), as in `wrap` (ADR 0003).

## Consequences

- `sentence_count` is linear, standard library only, independent of locale and Python
  version, and reuses the word rule of ADR 0001 instead of re-deciding it.
- Known divergences from a human count, all pinned in the table: a listed title at the end of
  a sentence (`"He was a Dr. He was tired."` is one), an unlisted abbreviation before a number
  or a capital (`"Approx. 5 people came."` is two), headings and list items without a
  terminator (merged with the next line), and sentences that start with a lower-case letter
  (merged with the one before).
- Adding an abbreviation to the list is a change of this rule: it changes this ADR, its table
  and the tests in one PR.
- The table below is the contract. `tests/test_counts.py` reads it from this file and checks
  every row against `sentence_count`, so the table and the code cannot drift apart silently.

## Cases

Inputs are Python string literals; Count is `sentence_count(input)`.

| Input | Count | Case |
|-------|-------|------|
| `""` | 0 | empty text |
| `"   \n\t"` | 0 | whitespace only |
| `"..."` | 0 | ellipsis only |
| `"!? -- ;"` | 0 | punctuation only |
| `"Hello"` | 1 | no terminator |
| `"Hello."` | 1 | one sentence |
| `"Hello. World."` | 2 | two sentences |
| `"Hello! World? Yes."` | 3 | `!`, `?` and `.` |
| `"Hello. World"` | 2 | last sentence without terminator |
| `"Hello.World."` | 1 | no space after the dot |
| `"Wait!!! Really?!"` | 2 | runs of terminators count once |
| `"Hello . World"` | 2 | space before the dot |
| `"Pi is 3.14. It is irrational."` | 2 | decimal number |
| `"It costs $5. Then it rose."` | 2 | number before the dot |
| `"Visit example.com today."` | 1 | dot inside a domain |
| `"It was 1999. 2000 came next."` | 2 | next sentence starts with a digit |
| `"Use e.g. apples."` | 1 | abbreviation before a lower-case word |
| `"Use e.g. Apples."` | 1 | listed abbreviation before a capital |
| `"Fruit (i.e. Apples) is good."` | 1 | listed abbreviation after a bracket |
| `"Compare cf. Smith vs. Jones."` | 1 | `cf.` and `vs.` |
| `"Dr. Smith is here."` | 1 | title |
| `"Mr. and Mrs. Smith left. They waved."` | 2 | titles, then a real sentence end |
| `"Ms. Lee met Prof. Kim."` | 1 | `Ms.` and `Prof.` |
| `"DR. SMITH IS HERE."` | 1 | abbreviations ignore case |
| `"The U.S.A. is big."` | 1 | dotted abbreviation before a lower-case word |
| `"I live in the U.S.A. It is big."` | 2 | dotted abbreviation before a capital |
| `"Apples, pears, etc. are fruit."` | 1 | `etc.` before a lower-case word |
| `"Apples, pears, etc. Then we left."` | 2 | `etc.` before a capital ends the sentence |
| `"He was a Dr. He was tired."` | 1 | known divergence: listed title at a sentence end |
| `"Approx. 5 people came."` | 2 | known divergence: unlisted abbreviation before a digit |
| `"Wait... what?"` | 1 | ellipsis before a lower-case word |
| `"I see... Let us go."` | 2 | ellipsis before a capital |
| `"I see… Let us go."` | 2 | Unicode ellipsis |
| `"Wait… what?"` | 1 | Unicode ellipsis before a lower-case word |
| `"And then..."` | 1 | trailing ellipsis |
| `"...and then it ended."` | 1 | leading ellipsis |
| `"Hello?!..."` | 1 | mixed run at the end |
| `"“Help!” he cried."` | 1 | closing quote, then a lower-case word |
| `"He said “Stop.” Then he left."` | 2 | closing quote, then a capital |
| `"(It rained.) We stayed."` | 2 | closing bracket |
| `"what? yes."` | 1 | lower-case after `?` continues the sentence |
| `"Line one\nLine two"` | 1 | a newline is not a terminator |
| `"One.\nTwo."` | 2 | a newline is whitespace after the dot |
| `"Title\n\nBody text."` | 1 | a blank line is not a terminator |
| `"Привет. Как дела?"` | 2 | Cyrillic |
| `"¿Qué? ¡Sí!"` | 2 | opening `¡` before the capital |
| `"你好。再见。"` | 2 | full-width terminators need no space |
| `"Done.\U0001f642 Next."` | 1 | emoji right after the dot |
