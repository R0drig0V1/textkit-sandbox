# Changelog

## Unreleased

- Added `char_freq` in `textkit.counts`: per-character counts of non-whitespace characters, case-sensitive, in order of first occurrence.
- Added `reading_time` in `textkit.counts`: whole minutes to read a text, `ceil(word_count / wpm)`, `wpm=200` by default; 0 for no words, `wpm < 1` raises `ValueError` (ADR 0004).
- Added `slug_title`: slug cut to at most `max_len` characters, never ending in `-`.
- Added `slugify`: lower-case ASCII slug with runs of other characters turned into one `-`.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_camel_case`: converts snake_case or kebab-case names to camelCase (`HTTP_server` -> `httpServer`).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case names to snake_case (ADR 0001).
- Added `truncate`: shortens text to exactly `width` code points, ending in a suffix when cut.
- Added `word_count` in the new module `textkit.counts`: counts words by the rule of ADR 0002.
- Added `wrap`: splits text into lines of at most `width` code points at whitespace; existing newlines are reflowed (ADR 0003).
