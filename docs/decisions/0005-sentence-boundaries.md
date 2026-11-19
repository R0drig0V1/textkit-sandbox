<!-- 0005-sentence-boundaries: where a sentence ends for textkit.counts.sentence_count (abbreviations, ellipses, decimals). -->
# 0005. Where a sentence ends

## Context

`textkit.counts.sentence_count(text)` (plan task T2.2) has to decide where a sentence ends.
Splitting on every `.`, `!` and `?` counts `"3.14"` as two sentences, `"e.g."` as two,
`"Dr. Smith arrived."` as two and `"Wait... what?"` as four. The cases readers will ask about
are abbreviations (`"e.g."`, `"Dr."`), ellipses (`"..."`, `"…"`), runs such as `"?!"`,
decimals, and text with no terminal punctuation at all. Full sentence segmentation needs a
trained model or a large dictionary, which the standard-library-only rule of `textkit` rules
out. So the rule has to be small, predictable and stated without reference to the
implementation. Every case below is a test.

## Decision

1. **Terminator runs.** The terminators are `.`, `!`, `?` and `…` (U+2026). A *terminator
   run* is a maximal run of them, together with any closing quotes or brackets right after
   it (`"`, `'`, `”`, `’`, `»`, `)`, `]`, `}`). A run ends at most one sentence, so `"?!"`,
   `"!!!"` and `"..."` each count once.
2. **Whitespace after the run.** A run can end a sentence only when whitespace or the end
   of the text comes right after it. That is why the dots of `"3.14"` and `"v2.0"`, the
   inner dot of `"e.g."` and the dot of `"Hello.World"` never end a sentence. No
   number-specific rule is needed.
3. **Abbreviations.** A run that is a single `.` does not end a sentence when the word
   before it is a known abbreviation. The word is the non-whitespace text before the dot,
   with leading opening quotes and brackets removed, compared after `casefold()`. The list
   is fixed:
   - titles that come before a name: `Mr`, `Mrs`, `Ms`, `Dr`, `Prof`, `St`;
   - Latin abbreviations that introduce more text: `e.g`, `i.e`, `cf`, `vs`.
4. **Ellipses.** A run made only of dots, with two or more dots or a `…`, is an *ellipsis*.
   An ellipsis ends a sentence unless the next word starts with a lowercase letter
   (`str.islower()`): `"Wait... what?"` is one sentence and `"He left... Then she came."`
   is two. A run that mixes dots with `?` or `!` (`"...?"`) is not an ellipsis and follows
   rule 2 only.
5. **Sentences need a word.** A sentence must contain at least one word under the word rule
   of docs/decisions/0002-what-counts-as-a-word.md, that is, at least one character for
   which `str.isalnum()` is true. Punctuation with no word before it ends nothing:
   `""`, `"..."` and `"?!"` give 0, and in `"Ready? . Go"` the lone dot is not a sentence.
   Words after the last sentence end, or in a text with no terminator at all, make one
   more sentence: `"Hello world"` is 1.
6. **Nothing else ends a sentence.** Newlines, semicolons, colons and dashes do not.
   `sentence_count(text)` is the number of sentences. Text that is not a `str` raises
   `TypeError`, as in `word_count`.

Why a fixed abbreviation list rather than a heuristic such as "a dot followed by a lowercase
word does not end a sentence": the heuristic gets `"Dr. Smith"` wrong (an uppercase word
follows), and it would count text written all in lowercase (`"hello. world."`) as a single
sentence. A list is predictable, and a reader can check it. The list stays small because
every entry is also a word that can end a sentence (`"I saw the dr."`). Only abbreviations
that almost never end one are on it. The lowercase test is used only for ellipses, where
trailing off (`"I think... maybe"`) and a pause between two sentences are both common, and
the case of the next word is the only signal available without a dictionary.

## Consequences

- `"etc."` is not on the list: it often ends a sentence (`"apples, pears, etc."`), so
  `"We bought apples, etc. Then we left."` is 2, and so is `"apples, etc. and pears"`.
  Accepted. Adding it would merge every sentence that ends with "etc.".
- Abbreviations missing from the list (`"approx."`, `"Fig."`, `"a.m."` before a space) end
  a sentence when a space follows. Accepted. Extending the list is an additive change to
  this ADR, its table and the tests.
- A listed abbreviation that really ends a sentence (`"I saw the dr. Then I left."`) merges
  two sentences into one.
- Missing whitespace hides a sentence end: `"Hello.World"` and `"Stop!Go"` are 1.
- A closing quote does not stop the count: `"'Stop!' he said."` is 2, because a run with a
  closer and then whitespace ends a sentence whatever follows. Telling dialogue tags apart
  would need the lowercase heuristic rejected above.
- An ellipsis before a digit or an uppercase word ends a sentence (`"Wait... 3 more"` is 2).
  So does one before a word of a script without case, since only a lowercase letter keeps
  the sentence open.
- Terminators of other scripts (`。`, `！`, `？`, `؟`) are not recognised: a Chinese or Arabic
  text counts as one sentence. This matches the word rule, which leaves those scripts out
  of scope too.
- No Unicode normalization is applied. The rule looks only at terminators, closers,
  whitespace and `str.isalnum`, so NFC and NFD forms of the same text give the same count.

## Cases

Inputs are Python string literals. `tests/test_counts.py` tests every row and checks that this
table and its own case list stay identical.

| Input | Count | Why |
|-------|-------|-----|
| `""` | 0 | empty text |
| `"   \n\t  "` | 0 | whitespace only |
| `"..."` | 0 | an ellipsis with no word is not a sentence |
| `"?!"` | 0 | punctuation only |
| `"Hello world"` | 1 | no terminal punctuation: the words are one sentence |
| `"Hello world."` | 1 | one terminated sentence |
| `"One. Two. Three."` | 3 | three sentences |
| `"Hi! How are you?"` | 2 | `!` and `?` end sentences |
| `"What?! No way."` | 2 | a run such as `?!` ends one sentence |
| `"Really?!?! Yes!!!"` | 2 | longer runs still end one sentence each |
| `"Pi is 3.14 exactly."` | 1 | a decimal point has no space after it |
| `"Version v2.0 is out. Get it!"` | 2 | dots inside a word do not end a sentence |
| `"e.g."` | 1 | an abbreviation alone is one sentence |
| `"Dr."` | 1 | an abbreviation alone is one sentence |
| `"Use fruit, e.g. apples, daily."` | 1 | `e.g.` before a space does not end a sentence |
| `"Ask Dr. Smith. He knows."` | 2 | `Dr.` before a name does not end a sentence |
| `"Mr. and Mrs. Smith arrived."` | 1 | several abbreviations in one sentence |
| `"(Dr. Who is here.) Next."` | 2 | opening bracket before an abbreviation, closer after `.` |
| `"I.e. it works."` | 1 | abbreviations are matched without case |
| `"We bought apples, etc. Then we left."` | 2 | `etc.` is not on the list |
| `"Wait... what?"` | 1 | ellipsis before a lowercase word continues the sentence |
| `"He left... Then she came."` | 2 | ellipsis before an uppercase word ends the sentence |
| `"Wait… what?"` | 1 | the `…` character is an ellipsis too |
| `"The end…"` | 1 | ellipsis at the end of the text |
| `"So...?"` | 1 | a run mixing dots and `?` is not an ellipsis |
| `"He said \"Stop!\" Then he left."` | 2 | a closing quote belongs to the run before it |
| `"'Stop!' he said."` | 2 | a closer then a space ends a sentence whatever follows |
| `"Ready? . Go"` | 2 | a lone dot with no word is not a sentence |
| `"Hello.World"` | 1 | no space after the dot |
| `"Line one\nLine two"` | 1 | newlines do not end sentences |
| `"Ñandú. Café."` | 2 | non-ASCII words |
