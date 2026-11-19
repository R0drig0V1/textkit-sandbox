<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-what-counts-as-a-word.md) | What counts as a word (`word_count` and the shared tokenizer) |
| [0002](0002-to-snake-case-capital-runs.md) | How `to_snake_case` splits runs of capitals and digits |
| [0003](0003-wrap-reflows-existing-newlines.md) | `wrap` treats existing newlines as spaces (reflow) |
| [0004](0004-reading-time-rounds-up.md) | `reading_time` rounds up to whole minutes; 0 only for text with no words |
