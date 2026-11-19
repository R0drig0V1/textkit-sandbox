# Changelog

## Unreleased

- Added `is_palindrome`: tells whether text is a palindrome, ignoring case, accents, spaces and punctuation.
- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_snake_case`: converts camelCase, PascalCase and kebab-case names to snake_case (ADR 0002).
- Added `truncate`: cuts text to an exact width, ending in a suffix (`...` by default).
- Added `word_count`: counts the words in a text, following ADR 0001.
