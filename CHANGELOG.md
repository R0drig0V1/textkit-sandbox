# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character (case-sensitive).
- Added `is_palindrome`: tells whether text is a palindrome, ignoring case, accents, spaces and punctuation.
- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_snake_case`: converts camelCase, PascalCase and kebab-case names to snake_case (ADR 0002).
- Added `truncate`: cuts text to an exact width, ending in a suffix (`...` by default).
- Added `word_count`: counts the words in a text, following ADR 0001.
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are word separators (ADR 0003).
