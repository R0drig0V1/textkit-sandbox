# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `char_freq` in `textkit.counts`: counts each non-whitespace character, case-sensitive, keys in order of first occurrence.
- Added `reading_time` in `textkit.counts`: whole minutes to read a text, from `word_count`, rounded up (ADR "Reading time rounding").
- Added the `python3 -m textkit` command line.
- Added `sentence_count` in `textkit.counts`: counts sentences; listed abbreviations such as `Dr.` and `e.g.` never end one, and ellipses and `etc.` end one unless a lower-case word follows (ADR "Sentence boundaries: abbreviations and ellipses").
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `to_camel_case`: snake_case or kebab-case to camelCase (`"user_id"` -> `"userId"`).
- Added `to_kebab_case`: camelCase, PascalCase or snake_case to kebab-case, built on
  `to_snake_case` (`"HTTPServer"` -> `"http-server"`).
- Added `to_snake_case` (new module `textkit.cases`): camelCase, PascalCase and kebab-case to
  snake_case; runs of capitals split as decided in
  the ADR "How `to_snake_case` splits runs of capitals".
- Added `truncate`: shortens text to a width, suffix included.
- Added `word_count` in the new module `textkit.counts`: counts words, keeping hyphenated words, contractions and numbers such as `3.14` whole (ADR "What counts as a word").
- Added `wrap`: splits text into lines of at most a width at spaces, reflowing existing line breaks (ADR "`wrap` reflows text").
