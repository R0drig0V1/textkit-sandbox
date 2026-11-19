# Changelog

## Unreleased

- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `slugify`: turns text into an ASCII lower-case slug joined by `-` (non-ASCII is dropped).
- Added `word_count` in the new module `textkit.counts`: counts words by the rule of ADR 0001.
- Added `truncate`: shortens text to exactly `width` characters, suffix included; raises `ValueError` when `width` is smaller than the suffix.
- Added `to_snake_case` (new module `textkit.cases`): converts camelCase, PascalCase and kebab-case names to snake_case; acronyms stay whole (ADR 0002).
- Added `strip_accents`: removes combining marks (NFD, drop category Mn, recompose with NFC).
- Added `char_freq` in `textkit.counts`: counts each non-whitespace character (`str.isspace()`), case-sensitive, without normalising.
- Added `wrap`: splits text into lines of at most `width` characters at whitespace, keeping existing line breaks (ADR 0003).
- Added `to_camel_case` in `textkit.cases`: converts snake_case and kebab-case names to camelCase; words are split as in `to_snake_case` (ADR 0002), so PascalCase and acronyms are normalised (`"HTTPServer"` -> `"httpServer"`).
