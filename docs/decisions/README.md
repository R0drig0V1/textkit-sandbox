<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-word-rule.md) | What counts as a word: letters and digits joined by `-`, `'`, `’`, and `.`/`,` between digits (`word_count`) |
| [0002](0002-splitting-runs-of-capitals.md) | How `to_snake_case` splits identifiers: runs of capitals, digits, `_`/`-` separators |
| [0003](0003-wrap-newlines.md) | `wrap` reflows: newlines and other ASCII whitespace are break points, not kept; no-break space is not a break point |
| [0004](0004-reading-time-rounding.md) | How `reading_time` rounds to whole minutes: ceiling, 0 for no words, at least 1 otherwise |
