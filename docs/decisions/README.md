<!-- Index of architecture decision records. -->
# Architecture decision records

One file per decision, `NNNN-title.md`, with Context / Decision / Consequences.

| # | Decision |
|---|----------|
| [0001](0001-to-snake-case-word-boundaries.md) | Word boundaries in `to_snake_case`: runs of capitals and digits |
| [0002](0002-word-count-what-counts-as-a-word.md) | What counts as a word in `word_count` |
| [0003](0003-wrap-existing-newlines.md) | `wrap` treats existing newlines (and all whitespace) as spaces: text is reflowed |
| [0004](0004-reading-time-rounding.md) | `reading_time` rounds up to whole minutes: empty text is 0, under one minute is 1 |
| [0005](0005-sentence-count-abbreviations-and-ellipses.md) | Where `sentence_count` ends a sentence: abbreviations, ellipses, lower case |
| [0006](0006-error-hierarchy.md) | `InvalidValueError` is a `TextkitError`, not a `ValueError`: an escaping `ValueError` is a bug |
| [0006](0006-template-missing-names.md) | `textkit.template`: a missing name is an error in `{{ }}` and `for`, false in `if` |
