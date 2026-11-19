# Changelog

## Unreleased

- Added `slugify`: lower-case ASCII slug (non-ASCII removed, other runs become `-`).
- Added `char_freq`: counts each non-whitespace character of a text, case-sensitive, keys in order of first occurrence.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase (`"user_id"` -> `"userId"`).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `truncate`: cuts text to an exact width, suffix included; raises `ValueError` when the width is smaller than the suffix.
- Added `word_count`: counts the words in a text, following ADR 0001 (hyphens, apostrophes, numbers).
