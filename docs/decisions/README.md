<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-what-counts-as-a-word.md) | What counts as a word: letters, digits and marks; `-` and apostrophes join, `.`/`,` join digits |
| [0002](0002-snake-case-word-splitting.md) | Word splitting in `to_snake_case`: runs of capitals, digits and separators |
| [0003](0003-wrap-newlines-are-separators.md) | `wrap` treats existing newlines as word separators; it does not keep them |
