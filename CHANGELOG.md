# Changelog

## Unreleased

- Added `char_freq` in `textkit.counts`: counts each non-whitespace character, case-sensitive, keys in order of first occurrence.
- Added `is_palindrome`: tells whether text reads the same backwards, ignoring case, accents and symbols.
- Added `slug_title`: slug cut to a maximum length (character cut), never ending in `-`.
- Added the `python3 -m textkit` command line.
- Added `slugify`: turns text into a lower-case ASCII slug (non-ASCII removed, no normalization).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (accents) from text.
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase.
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case, splitting words like `to_snake_case` (ADR 0001).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `truncate`: shortens text to a width, ending in a suffix when cut.
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers count once (ADR 0002).
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are treated as spaces (ADR 0003).
