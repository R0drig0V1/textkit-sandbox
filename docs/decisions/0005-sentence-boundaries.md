<!-- ADR 0005: the sentence rule of textkit.counts.sentence_count (abbreviations, ellipses). -->
# 0005. Sentence boundaries: abbreviations and ellipses

## Context

`sentence_count(text)` (plan task T2.2) needs a definition of where a sentence ends.
Counting `.`, `!` and `?` overcounts on decimals (`"3.14"`), abbreviations (`"Dr. Smith"`,
`"e.g. a hammer"`), runs (`"?!"`, `"..."`) and punctuation-only text; ellipses are
ambiguous: `"Wait... what?"` is one sentence, `"I waited... Nobody came."` is two. A full
answer needs a language model or per-language abbreviation lists; textkit is standard
library only, so the rule has to be small, predictable and honest about its limits.
What counts as a word is ADR 0002's rule, reused here so the two functions agree.

## Decision

1. **Terminators** are `.`, `!`, `?` and `…` (U+2026). A maximal run of them (`"?!"`,
   `"..."`, `"!!!"`) is one terminator.
2. **A run cuts only when it is followed by whitespace or the end of the text**, after any
   closing quotes or brackets (`"` `'` `’` `”` `»` `)` `]` `}`), which stay in the sentence
   they close. So `"3.14"`, `"example.com"`, `"e.g.,"` and `"One.Two"` never cut.
3. **A sentence is a piece that contains at least one word** (ADR 0002, `word_count` > 0).
   Text after the last cut counts even without a terminator (`"Hello"` is 1); pieces made of
   punctuation only (`"!!! ... ?"`) count 0.
4. **Abbreviations.** A single `.` after one of these, compared case-insensitively, does not
   cut: `Mr`, `Mrs`, `Ms`, `Dr`, `Prof`, `Sr`, `Jr` (titles, which precede a name) and `vs`,
   `cf`, `e.g`, `i.e` (which introduce what follows). The abbreviation must be a token on its
   own (`"2dr."` is not one). `etc.` is **not** in the list: it usually ends a list and, as
   often as not, the sentence.
5. **Ellipses.** A run made only of `.` and `…`, other than a single `.`, cuts only when the
   next non-space character, after any opening quotes or brackets, is upper-case
   (`str.isupper`), or nothing follows. A run that contains `!` or `?` always cuts.

## Consequences

- Decimals, URLs, titles before names and the Latin abbreviations count as a reader would.
- Every other dotted abbreviation cuts: `"the U.S. and"` and `"Main St. is"` are two
  sentences, and so are initials (`"J. Smith"`). Adding entries is a change of this ADR.
- A title that ends a sentence joins it to the next: `"He is Smith Jr. She is not."` is 1.
- An ellipsis before a lower-case word, a digit or a script without case (CJK) never cuts;
  before a capitalised name or `"I"` it always does.
- `!` and `?` inside a quotation cut even when the sentence goes on: `"\"Why?\" he asked."`
  is 2.
- Newlines and blank lines are not boundaries: a heading without a period joins the next
  sentence. CJK terminators (`。`, `！`, `？`) are not recognised.
- No Unicode normalization; every character is looked at once, so the cost is linear apart
  from the `word_count` call on each piece.

## Table of cases

Tested row by row in `tests/test_counts.py` (`ADR_0005_CASES`, same order).

| Input (Python literal) | Count | Why |
|------------------------|-------|-----|
| `""` | 0 | empty text |
| `"Hello"` | 1 | no terminator, still a sentence |
| `"Hello world. Bye."` | 2 | `.` followed by a space cuts |
| `"Really?! Yes!!"` | 2 | a run of terminators is one terminator |
| `"It costs 3.14 dollars."` | 1 | `.` not followed by whitespace does not cut |
| `"Visit example.com today."` | 1 | same, in a domain name |
| `"One.Two"` | 1 | same, missing space |
| `"I met Dr. Smith. He was kind."` | 2 | `Dr.` is an abbreviation |
| `"Mr. and Mrs. Smith left."` | 1 | titles do not cut |
| `"DR. NO is a film."` | 1 | abbreviations match in any case |
| `"Use a tool, e.g. a hammer."` | 1 | `e.g.` does not cut |
| `"Fruit, i.e. apples, is good."` | 1 | `i.e.` does not cut |
| `"Cats vs. dogs."` | 1 | `vs.` does not cut |
| `"Bring pens, paper, etc. Then sit."` | 2 | `etc.` is not an abbreviation here |
| `"I live in the U.S. and it is big."` | 2 | limit: other dotted abbreviations cut |
| `"Wait... what happened?"` | 1 | ellipsis before lower case does not cut |
| `"I waited... Nobody came."` | 2 | ellipsis before a capital cuts |
| `"I waited… Nobody came."` | 2 | `…` (U+2026) is an ellipsis too |
| `"The end..."` | 1 | ellipsis at the end |
| `"He said \"Stop.\" Then he left."` | 2 | closing quote stays with its sentence |
| `"\"Why?\" he asked."` | 2 | limit: `?` in a quotation cuts |
| `"!!! ... ?"` | 0 | punctuation only |
| `"Hi. ... Bye."` | 2 | a punctuation-only piece is not a sentence |
| `"Line one\nLine two"` | 1 | newlines are not boundaries |
| `"First. \n\n Second."` | 2 | any whitespace after `.` cuts |
