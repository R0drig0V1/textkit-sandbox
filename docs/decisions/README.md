<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-what-counts-as-a-word.md) | What counts as a word (`word_count`, the shared tokenizer) |
| [0002](0002-snake-case-word-boundaries.md) | Word boundaries in `to_snake_case`: acronyms stay whole, digits stay with the previous word |
| [0003](0003-wrap-line-breaks-and-whitespace.md) | How `wrap` treats existing line breaks and whitespace |
| [0004](0004-where-a-sentence-ends.md) | Where a sentence ends (`sentence_count`): abbreviations, ellipses, decimals, quotes |
| [0005](0005-reading-time-rounding.md) | How `reading_time` rounds to whole minutes (ceiling, exact) and which `wpm` values it accepts |
