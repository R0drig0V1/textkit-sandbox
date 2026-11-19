<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-what-counts-as-a-word.md) | What counts as a word: letters, digits and marks; `-` and apostrophes join, `.`/`,` join digits |
| [0002](0002-snake-case-word-splitting.md) | Word splitting in `to_snake_case`: runs of capitals, digits and separators |
| [0003](0003-wrap-newlines-are-separators.md) | `wrap` treats existing newlines as word separators; it does not keep them |
| [0004](0004-reading-time-rounding.md) | Reading time rounds up to whole minutes: no words is 0, any text is at least 1 |
| [0005](0005-sentence-ends-abbreviations-and-ellipses.md) | Sentence ends for `sentence_count`: terminator runs before whitespace; lower-case continuation and a short title list |
