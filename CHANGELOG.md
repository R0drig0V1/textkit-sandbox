# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character (case-sensitive), keys in order of first occurrence.
- Added `reading_time`: whole minutes to read a text at `wpm` words per minute (default 200), rounded up; rounding in ADR 0004.
- Added `slugify`: turns text into a lower-case ASCII slug such as `hello-world`.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase (`user_id` -> `userId`).
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case, built on `to_snake_case` (ADR 0001).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case (word boundaries in ADR 0001).
- Added `word_count`: counts the words in a text; the word rule is ADR 0002.
- Added `truncate`: shortens text to a width, ending with a suffix when cut.
- Added `wrap`: splits text into lines of at most `width` characters at spaces (ADR 0003).
