<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-what-counts-as-a-word.md) | What counts as a word: alphanumeric runs joined by single hyphens/apostrophes, and digits by `.`/`,` |
| [0002](0002-snake-case-capital-runs.md) | How `to_snake_case` splits runs of capitals, digits and separators |
| [0003](0003-wrap-existing-newlines.md) | `wrap` reflows text: existing line breaks separate words like a space |
| [0004](0004-reading-time-rounding.md) | Reading time rounding: `ceil(words / wpm)`, so no words is 0 minutes and any text under a minute is 1 |
