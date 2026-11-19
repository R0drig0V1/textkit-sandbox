# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character of a text, case-sensitive, in order of first occurrence.
- Added `slug_title`: a slug cut to at most `max_len` characters that never ends in `-` (`slug_title("Hello, World!", 8)` -> `"hello-wo"`).
- Added `slugify`: turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase (`"user_id"` -> `"userId"`), splitting only on the separators of ADR 0002.
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case (`"HTTPServer"` -> `"http-server"`), built on `to_snake_case` and its ADR 0002 split.
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case, splitting runs of capitals as in ADR 0002.
- Added `truncate`: shortens text to a width, ending in a suffix when cut.
- Added `word_count`: counts the words in a text, following the word rule of ADR 0001.
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are reflowed (ADR 0003).
- Added the `python3 -m textkit` command line.
