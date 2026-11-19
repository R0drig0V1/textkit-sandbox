# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character (case-sensitive), keys in order of first occurrence.
- Added `slugify`: turns text into a lower-case ASCII slug such as `hello-world`.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case (word boundaries in ADR 0001).
- Added `word_count`: counts the words in a text; the word rule is ADR 0002.
- Added `truncate`: shortens text to a width, ending with a suffix when cut.
