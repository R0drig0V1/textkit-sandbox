# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character, case-sensitive, keys in order of first occurrence.
- Added `is_palindrome`: tells whether text is a palindrome, ignoring case, accents (via `strip_accents`) and non-alphanumerics.
- Added `reading_time`: whole minutes to read a text at `wpm` words per minute (default 200), rounded up; 0 only for a text with no words (ADR 0004).
- Added `slug_title`: a slug cut to at most `max_len` characters that never ends in `-`.
- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (accents) via NFD, returns NFC.
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase.
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case, built on `to_snake_case` (ADR 0001).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case (ADR 0001).
- Added `truncate`: cuts text to a width, ending in a suffix (`...` by default).
- Added `word_count`: counts the words in a text, by the rule of ADR 0002.
- Added `wrap`: splits text into lines of at most `width` characters, breaking between words.
- Added the `python3 -m textkit` command line.
- Added `python3 -m textkit --version`.
