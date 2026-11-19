<!-- ADR 0005: where sentence_count finds sentence boundaries (abbreviations, ellipses). -->
# 0005. Sentence boundaries: abbreviations and ellipses

## Context

`sentence_count(text) -> int` (plan task T2.2) lives in `textkit/counts.py` next to
`word_count`, whose word rule is ADR 0002. "Split on `.`, `!` and `?`" is not enough: it
counts `"Dr. Smith arrived."` and `"Fruit, e.g. apples."` as two sentences, `"3.14"` as two,
`"..."` as several, and `"?!"` as sentences with nothing in them. The plan asks for a decision
on abbreviations (`"e.g."`, `"Dr."`) and ellipses, and the standard-library-only rule excludes
a trained sentence segmenter, so the rule must be a small, predictable heuristic.

## Decision

`sentence_count` scans the text for **boundaries** and counts the pieces between them that
contain at least one word.

1. **Terminators** are `.`, `!`, `?` and the ellipsis character `…` (U+2026). A run of
   consecutive terminators (`"?!"`, `"..."`, `".…"`) is one candidate boundary.
2. A candidate is a **boundary** only when, after the run and any closing quotes or brackets
   (`"` `'` `”` `’` `)` `]` `}` `»`), comes whitespace or the end of the text. So `"3.14"`,
   `"U.S.A"` and `"end.Next"` contain no boundary.
3. It is **not** a boundary when the next word starts with a lowercase letter
   (`str.islower()` on the first alphanumeric character after the whitespace and any
   opening quotes or brackets). This is how ellipses and quoted questions continue a
   sentence: `"Wait... what happened?"` and `"'Really?' she asked."` are one sentence each.
4. **Abbreviations.** When the run is a single `.`, it is not a boundary if the
   whitespace-delimited token just before it (opening quotes and brackets removed) is:
   - one of `Dr`, `Mr`, `Mrs`, `Ms`, `Prof`, `vs`, compared case-insensitively
     (`str.casefold`): titles that precede a name, and "versus"; or
   - one or more single letters joined by dots (`str.isalpha`): initials and Latin
     abbreviations such as `J`, `e.g`, `i.e`, `U.S.A`.
   The list is closed and English. Abbreviations that often end a sentence (`etc.`, `Jr.`,
   `St.`, `Inc.`) are left out, because merging two real sentences is the worse error for
   them.
5. **Ellipses** (`...`, `…`, or any run of dots) are terminators like `.` but never
   abbreviations: `"Wait... Then it rained."` is two sentences; rule 3 keeps
   `"Wait... what"` as one.
6. **A sentence needs at least one word** by the rule of ADR 0002, checked with `word_count`
   on each piece. A piece with no word (`"?!"`, `"..."`, `"!!!"`, `"🙂."`) is not a sentence,
   and text after the last boundary is a sentence if it has a word, terminated or not. So
   `""` and whitespace give 0, and `"Hello world"` gives 1.

Line breaks are whitespace, not boundaries: a list of lines without terminators is one
sentence. `sentence_count` raises `TypeError` for anything that is not a `str`.

### Relation to ADR 0002

A sentence is made of words in the sense of ADR 0002: rule 6 calls `word_count`, so a
change of the word rule changes which pieces count. Boundaries, though, are found on the raw
text, not on ADR 0002 words, because ADR 0002 drops the dots that matter here: it splits
`"e.g."` into the words `e` and `g`, and treats a `.` between digits as part of a word. Rule
2 agrees with it on numbers: `"3.14"` is one word and contains no boundary.

## Consequences

- Ordinary English prose counts the way a reader expects: titles before names, initials,
  `e.g.`/`i.e.`, decimals, quoted speech and trailing-off ellipses do not split sentences;
  `?!` and `...` end a sentence once.
- Known miscounts, accepted for a rule that fits in a few lines:
  - a sentence that really ends with an initial or a listed abbreviation is merged with the
    next one (`"Born in the U.S. He moved."` is 1; so is `"I want plan B. Now."`);
  - text written all in lowercase is under-counted (`"hi. bye."` is 1), by rule 3;
  - abbreviations outside the list split a sentence before a capitalised word
    (`"Approx. Ten people"` is 2);
  - terminators of other scripts (`。`, `؟`, `।`) are not recognised, so such text counts as
    one sentence per Latin terminator only.
- Extending the abbreviation list or the terminators is a change of behaviour: it needs a new
  ADR that supersedes this one and an update of the table below.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that this
table and its own list of cases are the same.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"   \n\t"` | 0 | whitespace only has no word |
| `"Hello world"` | 1 | text with no terminator is one sentence |
| `"Hello world."` | 1 | one terminated sentence |
| `"One. Two! Three? Four"` | 4 | several sentences; the last one is not terminated |
| `"Line one\nLine two"` | 1 | a line break is not a boundary |
| `"?!"` | 0 | terminators with no word are not a sentence |
| `"Really?! Yes."` | 2 | a run of terminators is one boundary |
| `"..."` | 0 | an ellipsis alone has no word |
| `"…"` | 0 | the ellipsis character alone has no word |
| `"Wait... Then it rained."` | 2 | an ellipsis before a capital ends a sentence |
| `"Wait... what happened?"` | 1 | an ellipsis before a lowercase word does not |
| `"Wait… Then it rained."` | 2 | `…` (U+2026) works like `...` |
| `"e.g."` | 1 | an abbreviation alone is a sentence: it has words |
| `"Fruit, e.g. Fuji apples, is sweet."` | 1 | the dot of `e.g.` is not a boundary, even before a capital |
| `"Dr."` | 1 | a title alone is a sentence: it has a word |
| `"Dr. Smith is in. He waits."` | 2 | the dot of `Dr.` is not a boundary |
| `"Ask MRS. Lee."` | 1 | the abbreviation list ignores case |
| `"J. R. R. Tolkien wrote it."` | 1 | initials are not boundaries |
| `"Born in the U.S. He moved."` | 1 | known miscount: a sentence ending in initials merges |
| `"Pi is 3.14. Yes."` | 2 | a dot between digits is not a terminator |
| `"Chapter 1. Intro"` | 2 | a digit is not an initial |
| `"end.Next"` | 1 | a terminator not followed by whitespace is not a boundary |
| `'He said "Stop." Then he left.'` | 2 | closing quotes may follow the terminator |
| `"'Really?' she asked."` | 1 | a lowercase word after the quote continues the sentence |
| `"Hi. !!! Bye."` | 2 | a piece with no word is not a sentence |
| `"🙂."` | 0 | emoji are not words (ADR 0002), so this is not a sentence |
