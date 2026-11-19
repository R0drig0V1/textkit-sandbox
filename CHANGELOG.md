# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (accents) via NFD, returns NFC.
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase.
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case (ADR 0001).
- Added `truncate`: cuts text to a width, ending in a suffix (`...` by default).
- Added `word_count`: counts the words in a text, by the rule of ADR 0002.
