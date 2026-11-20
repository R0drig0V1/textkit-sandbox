<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-to-snake-case-word-boundaries.md) | How `to_snake_case` splits names into words (runs of capitals, digits, separators) |
| [0002](0002-what-counts-as-a-word.md) | What counts as a word (`word_count`, the shared tokenizer) |
| [0003](0003-wrap-reflows-existing-newlines.md) | `wrap` reflows text: existing newlines are separators like spaces |
| [0004](0004-reading-time-rounds-up.md) | `reading_time` rounds up to whole minutes: no words is 0, under one minute is 1 |
