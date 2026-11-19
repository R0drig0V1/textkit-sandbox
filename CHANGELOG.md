# Changelog

## Unreleased

- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_snake_case` (new module `textkit.cases`): camelCase, PascalCase and kebab-case to
  snake_case; runs of capitals split as decided in
  the ADR "How `to_snake_case` splits runs of capitals".
- Added `truncate`: shortens text to a width, suffix included.
- Added `word_count` in the new module `textkit.counts`: counts words, keeping hyphenated words, contractions and numbers such as `3.14` whole (ADR "What counts as a word").
