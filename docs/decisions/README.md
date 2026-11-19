<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-wrap-reflows-existing-newlines.md) | `wrap` treats existing newlines as spaces and reflows the text |
| [0002](0002-what-counts-as-a-word.md) | What counts as a word (`word_count`): hyphens, apostrophes and digit separators join, everything else separates |
| [0003](0003-snake-case-capital-runs.md) | How `to_snake_case` splits runs of capitals, digits and separators |
| [0004](0004-reading-time-rounding.md) | `reading_time` rounds the word count up to whole minutes; text with no words is 0 |
