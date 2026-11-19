# Changelog

## Unreleased

- Added `slug_title`: builds a slug of at most `max_len` characters that never ends in `-`.
- Added `char_freq` in `textkit.counts`: counts each non-whitespace character, case-sensitive, keys in order of first occurrence.
- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase (separators as in ADR 0001).
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case, built on `to_snake_case` (ADR 0001).
- Added `truncate`: shortens text to a given width, ending in a suffix (`...` by default).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case (ADR 0001).
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers such as `3.14` count once (ADR 0002).
