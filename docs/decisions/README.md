<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-wrap-reflows-existing-newlines.md) | `wrap` treats existing newlines as spaces and reflows the text |
| [0002](0002-what-counts-as-a-word.md) | What counts as a word (`word_count`): hyphens, apostrophes and digit separators join, everything else separates |
| [0003](0003-snake-case-capital-runs.md) | How `to_snake_case` splits runs of capitals, digits and separators |
| [0004](0004-reading-time-rounding.md) | `reading_time` rounds the word count up to whole minutes; text with no words is 0 |
| [0005](0005-sentence-boundaries.md) | Where a sentence ends (`sentence_count`): abbreviations, ellipses and decimals |
| [0006](0006-what-is-an-email-address.md) | What `is_email` accepts: one `@`, a dot-atom local part, a host-name domain of two or more labels, ASCII only, 64/254 length limits |
| [0007](0007-pluralize-rules.md) | Which plural rules `pluralize` covers (`-s`, `-es`, `-ies`, an irregular table) and how it keeps the input's case |
