# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug (non-ASCII removed, no normalization).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `truncate`: shortens text to a width, ending in a suffix when cut.
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers count once (ADR 0001).
