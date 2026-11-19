# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character of a text, case-sensitive, in order of first occurrence.
- Added `slugify`: turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case, splitting runs of capitals as in ADR 0002.
- Added `word_count`: counts the words in a text, following the word rule of ADR 0001.
