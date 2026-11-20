# Changelog

## Unreleased

- Added `slugify`: lower-case ASCII slug with runs of other characters turned into one `-`.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case names to snake_case (ADR 0001).
- Added `truncate`: shortens text to exactly `width` code points, ending in a suffix when cut.
- Added `word_count` in the new module `textkit.counts`: counts words by the rule of ADR 0002.
