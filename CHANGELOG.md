# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug (non-ASCII removed, no normalization).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `truncate`: shortens text to a width, ending in a suffix when cut.
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase.
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `strip_accents`: removes combining marks (accents) from text.
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers count once (ADR 0002).
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are treated as spaces (ADR 0003).
