# Changelog

## Unreleased

- Added `slug_title`: `slugify` output cut to at most `max_len` characters, with trailing `-` stripped; raises `ValueError` when `max_len < 0`.
- Added `slugify`: lower-case ASCII slug (non-ASCII removed, other runs become `-`).
- Added `char_freq`: counts each non-whitespace character of a text, case-sensitive, keys in order of first occurrence.
- Added the `python3 -m textkit` command line.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase (`"user_id"` -> `"userId"`).
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case, with the word rule of `to_snake_case` (ADR 0002).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `truncate`: cuts text to an exact width, suffix included; raises `ValueError` when the width is smaller than the suffix.
- Added `word_count`: counts the words in a text, following ADR 0001 (hyphens, apostrophes, numbers).
- Added `wrap`: splits text into lines of at most a width at spaces; existing newlines are treated as spaces (ADR 0003).
