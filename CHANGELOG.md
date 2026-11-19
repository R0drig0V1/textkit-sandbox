# Changelog

## Unreleased

- Added `slugify`: lower-case ASCII slug (non-ASCII removed, other runs become `-`).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `truncate`: cuts text to an exact width, suffix included; raises `ValueError` when the width is smaller than the suffix.
- Added `word_count`: counts the words in a text, following ADR 0001 (hyphens, apostrophes, numbers).
- Added `wrap`: splits text into lines of at most a width at spaces; existing newlines are treated as spaces (ADR 0003).
