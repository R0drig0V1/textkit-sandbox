<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-snake-case-word-boundaries.md) | Word boundaries in `to_snake_case`: acronym runs, digits, separators |
| [0002](0002-what-counts-as-a-word.md) | What counts as a word (`word_count` and the shared tokenizer) |
| [0003](0003-wrap-treats-newlines-as-spaces.md) | `wrap` treats existing newlines as spaces (reflow) |
| [0004](0004-reading-time-rounds-up.md) | `reading_time` rounds up to whole minutes (empty text 0, any word at least 1) |
| [0005](0005-sentence-boundaries.md) | Sentence boundaries in `sentence_count`: abbreviations, ellipses, a sentence needs a word |
