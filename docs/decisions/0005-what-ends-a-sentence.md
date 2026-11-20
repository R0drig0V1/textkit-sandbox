<!-- ADR 0005: the sentence rule of sentence_count (T2.2): terminators, abbreviations, ellipses. -->
# 0005. What ends a sentence

## Context

`sentence_count(text)` (T2.2, `textkit/counts.py`) needs a rule for where one sentence ends
and the next begins. Splitting on every `.`, `!` and `?` is wrong in the cases readers care
about most: abbreviations (`"e.g."`, `"Dr."`), ellipses (`"..."`, `"…"`), numbers (`"3.14"`)
and domain names (`"example.com"`). A full solution needs a language model or per-language
dictionaries; this package is standard library only and must stay predictable. So the rule
below is a small set of deterministic heuristics, with its known miscounts listed in the
case table instead of hidden.

## Decision

Definitions, applied to code points with no Unicode normalization:

- **Word character**: `ch.isalnum()`, the same as in ADR 0002 (what counts as a word).
- **Terminator**: `.`, `!`, `?` or `…` (U+2026). A **terminator run** is a maximal run of
  terminators (`"?!"`, `"!!!"`, `"..."` are one run each).
- **Closer**: one of `"` `'` `”` `’` `)` `]` `}` `»`, which may follow a terminator run
  (`He said "Hi." Then...`).
- **Abbreviation**: one of `Dr`, `Mr`, `Mrs`, `Ms`, `Prof`, `St`, `vs`, `cf`, `e.g`, `i.e`,
  compared with `str.casefold()`.

A terminator run ends a sentence when all of these hold:

1. **End or space.** After the run and any closers comes the end of the text or a whitespace
   character (`str.isspace()`). So `"3.14"`, `"example.com"`, `"Hello.World"` and
   `"Wait...what"` contain no boundary.
2. **No lower-case continuation.** The first word character after the run is not lower case
   (`str.islower()`). So `"e.g. a hammer"`, `"etc. and more"`, `"Wait... what?"` and
   `"Help!" she cried` stay one sentence. Upper-case letters, digits and letters of scripts
   without case all allow the boundary. Opening punctuation (`"`, `(`, `¿`) is skipped when
   looking for that character.
3. **Not an abbreviation.** If the run is exactly one `.`, the characters before it, back to
   the nearest character that is neither a word character nor `.`, are not an abbreviation.
   So `"Dr. Smith"` and `"e.g. Python"` stay one sentence.

A sentence is the text between two boundaries (or the start or end of the text). Only
sentences that contain at least one word character are counted, so the last sentence counts
even without a terminator (`"One. Two"` is 2), and runs of punctuation alone are not
sentences (`"!!! ... ?"` is 0). `""` and text with no word character give 0.

Why these choices, where readers disagree:

- **Ellipses** get no rule of their own. `"..."` and `"…"` are terminator runs like `"?!"`;
  rule 2 decides: `"Wait... what?"` is 1, `"Wait... What?"` is 2. A leading ellipsis
  (`"...and then."`) ends nothing, since no word comes before it.
- **The abbreviation list is short on purpose.** It holds titles that are almost always
  followed by a capitalised name (`Dr`, `Mr`, `Mrs`, `Ms`, `Prof`, `St`), and Latin forms
  that are often followed by one (`e.g`, `i.e`, `cf`, `vs`). `etc` is left out because it
  often does end a sentence (`"pears, etc. Then we left."` is 2); rule 2 already keeps
  `"etc. and"` together. `Jr` and `Sr` are left out because they usually close a name at
  the end of a sentence. Any longer list is still incomplete and English only.
- **Known miscounts** are accepted rather than special-cased: an abbreviation at the real end
  of a sentence (`"Ask the Dr. Then go."` is 1), initials and dotted forms not in the list
  (`"J. R. R. Tolkien"` counts each initial; `"U.S. Army"` is 2), and a sentence that starts
  in lower case (`"Is it? yes."` is 1).
- **Line breaks** are whitespace with no meaning of their own: a heading without a full stop
  joins the next sentence (`"Title\n\nBody text."` is 1).
- **Other scripts' terminators** (`。`, `！`, `？`, `؟`, `।`) are not terminators in this
  version, so `"你好。再见。"` is 1. Adding them needs a new ADR that supersedes this one.

## Consequences

- `sentence_count` is a single left-to-right scan; the look-ahead for rule 2 is cached, so
  the scan stays linear even for long runs of punctuation.
- `sentence_count` uses neither `word_count` nor the shared tokenizer's `words`
  (`textkit/_tokens.py`): it needs ADR 0002's word character (`str.isalnum()`), not whole
  words. So a change to how words are joined does not change sentence counts.
- Changing the rule (a longer abbreviation list, other scripts) changes every count built on
  it and needs a new ADR that supersedes this one.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that
its list of cases equals this table.

| Input | Count |
|-------|-------|
| `""` | 0 |
| `"Hello"` | 1 |
| `"Hello."` | 1 |
| `"Hello. World."` | 2 |
| `"Hello! World? Yes."` | 3 |
| `"Really?!"` | 1 |
| `"Stop!!! Now."` | 2 |
| `"One. Two"` | 2 |
| `"3.14 is pi."` | 1 |
| `"Visit example.com today."` | 1 |
| `"Hello.World"` | 1 |
| `"Version 2. Then 3."` | 2 |
| `"Use a tool, e.g. a hammer."` | 1 |
| `"Use a tool, e.g. Python."` | 1 |
| `"Use i.e., this one."` | 1 |
| `"I met Dr. Smith. He was kind."` | 2 |
| `"Mr. and Mrs. Smith left."` | 1 |
| `"Apples, pears, etc. and more."` | 1 |
| `"Apples, pears, etc. Then we left."` | 2 |
| `"Wait... what?"` | 1 |
| `"Wait... What?"` | 2 |
| `"Wait… What?"` | 2 |
| `"Wait...what?"` | 1 |
| `"...and then."` | 1 |
| `"Hmm..."` | 1 |
| `'He said "Hi." Then he left.'` | 2 |
| `'"Help!" she cried.'` | 1 |
| `"(It works.) Good."` | 2 |
| `"¿Qué tal? Bien."` | 2 |
| `"Ñandú. Ñandú."` | 2 |
| `"Line one.\nLine two."` | 2 |
| `"Title\n\nBody text."` | 1 |
| `"Ask the Dr. Then go."` | 1 |
| `"J. R. R. Tolkien wrote it."` | 4 |
| `"U.S. Army"` | 2 |
| `"Is it? yes."` | 1 |
| `"你好。再见。"` | 1 |
| `"!!! ... ?"` | 0 |
| `" \n\t "` | 0 |
