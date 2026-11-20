<!-- ADR 0005: the sentence rule of textkit.counts.sentence_count (plan task T2.2). -->
# 0005. `sentence_count`: abbreviations and ellipses

## Context

`textkit.counts.sentence_count(text) -> int` (plan task T2.2) needs a rule for where a
sentence ends. Splitting on every `.`, `!` and `?` is wrong for the most common cases in
prose: decimals and domains (`"3.14"`, `"example.com"`), abbreviations (`"Dr. Smith"`,
`"e.g. Paris"`), ellipses (`"He paused... then left."`) and quoted speech
(`"\"Wow!\" he said."`). There is no exact rule without a language model of the text, so the
rule has to be a small, predictable heuristic whose wrong answers are written down. The word
rule of ADR 0002 (`word_count`, T1.5) already defines what a word is; this rule reuses it.

## Decision

1. **Terminators** are `.`, `!`, `?` and `…` (U+2026). A run of them in any mix (`"?!"`,
   `"..."`, `"!!!"`) is one end, so an ellipsis is a terminator like a full stop.
2. **A candidate end** is a terminator run, optionally followed by closing quotes or
   brackets (`"` `'` `”` `’` `)` `]` `}` `»`), followed by whitespace or the end of the text.
   A terminator followed by anything else (`"3.14"`, `"example.com"`, `"e.g.,"`) is not an
   end.
3. **Lower case continues the sentence.** A candidate end is cancelled when the next
   non-whitespace character is a lower-case letter (`str.islower()`). This covers ellipses
   inside a sentence (`"He paused... then left."`), quoted speech (`"\"Wow!\" he said."`) and
   abbreviations not in the list below that are followed by lower case (`"etc. and"`,
   `"a.m. on"`). Only that one character is looked at; an opening quote or a digit is not
   lower case.
4. **Abbreviations.** A candidate end whose terminator run is a single `.` is cancelled when
   the token before it (back to the previous whitespace, leading opening quotes and brackets
   removed, compared after `casefold()`) is one of `Dr`, `Mr`, `Mrs`, `Ms`, `Mx`, `Prof`,
   `vs`, `e.g`, `i.e`, or a single letter (an initial: `"J. R. R. Tolkien"`). The list holds
   only abbreviations that almost never end a sentence: titles come before a name, and
   `vs.`, `e.g.`, `i.e.` introduce something. Abbreviations that often do end one (`etc.`,
   `Jr.`, `St.`, `a.m.`, `U.S.`) are left out and behave like any word, relying on rule 3.
5. **A sentence has a word.** The text between two ends (or after the last one) is a
   sentence only if it contains at least one word by ADR 0002 (`_tokens.words`). Text after
   the last end counts even with no terminator (`"Hello"` is 1). `""`, whitespace only and
   punctuation only give 0, and a stray `"..."` between sentences adds nothing.
6. **Nothing else ends a sentence**: not newlines or blank lines, not `;` or `:`, and not
   other scripts' terminators (`"。"`, `"।"`). Non-`str` input raises `TypeError`.

## Consequences

- The common cases of English prose count as a reader expects, with no dependencies and no
  language data beyond nine abbreviations.
- Known wrong answers, pinned in the table so a change is deliberate:
  - A listed abbreviation at the real end of a sentence hides that end
    (`"I saw the Dr. Then I left."` is 1).
  - An unlisted abbreviation followed by a capitalised word is an end
    (`"I met John Smith Jr. He waved."` is right, `"We met St. Peter."` would be 2).
  - Text that starts its sentences in lower case is under-counted (`"first. second."` is 1).
  - A single letter before a full stop is taken as an initial (`"Plan B. Then"` is 1).
  - Headings and list items without terminators run into the next sentence
    (`"Title\n\nBody text"` is 1). Chinese and Japanese text is one sentence per paragraph
    unless it uses the ASCII terminators followed by whitespace.
- Changing the abbreviation list or any rule changes counts for existing text, so it means
  amending this ADR and its table. `tests/test_counts.py` tests every row below and checks
  that this table and the tests list the same cases.

## Cases

Inputs are Python string literals.

| Input | Count |
|-------|-------|
| `""` | 0 |
| `"   \n\t "` | 0 |
| `"..."` | 0 |
| `"!?! …"` | 0 |
| `"Hello"` | 1 |
| `"Hello."` | 1 |
| `"Hello. World."` | 2 |
| `"Is it? Yes! Good."` | 3 |
| `"Really?! Yes."` | 2 |
| `"Pi is 3.14. It is irrational."` | 2 |
| `"Visit example.com today."` | 1 |
| `"Version 1.2.3 is out. Get it."` | 2 |
| `"Dr. Smith arrived. He sat."` | 2 |
| `"Ask MR. Jones or mrs. Lee."` | 1 |
| `"Some cities, e.g. Paris, are big."` | 1 |
| `"Kramer vs. Kramer won. It is old."` | 2 |
| `"(Prof. Lee) Hi."` | 1 |
| `"J. R. R. Tolkien wrote it."` | 1 |
| `"We bought pens, etc. Then we left."` | 2 |
| `"We bought pens, etc. and paper."` | 1 |
| `"I met John Smith Jr. He waved."` | 2 |
| `"I saw the Dr. Then I left."` | 1 |
| `"Wait... What?"` | 2 |
| `"Wait… What?"` | 2 |
| `"He paused... then left."` | 1 |
| `"And so..."` | 1 |
| `"Hello. ... World."` | 2 |
| `"\"Wow!\" he said."` | 1 |
| `"He said \"Stop.\" Then he left."` | 2 |
| `"(It works.) Next one."` | 2 |
| `"first. second."` | 1 |
| `"Title\n\nBody text"` | 1 |
| `"Ça va? Oui."` | 2 |
| `"日本語。英語。"` | 1 |
