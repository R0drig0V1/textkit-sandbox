# Changelog

## Unreleased

- Added `slug_title`: a slug of at most `max_len` characters that never ends in `-` (character cut); raises `ValueError` when `max_len` is negative.
- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `truncate`: shortens text to a width, ending with a suffix when cut; raises `ValueError` when the width is smaller than the suffix.
- Added `to_camel_case`: converts snake_case and kebab-case identifiers to camelCase; a run of `-`/`_` counts as one separator, and input with no separator only has its first character lower-cased.
- Added `to_snake_case`: converts camelCase, PascalCase and kebab-case identifiers to snake_case ([ADR](docs/decisions/0003-snake-case-capital-runs.md)).
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are reflowed (ADR 0001).
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers such as `3.14` count as one (rule: [docs/decisions/0002-what-counts-as-a-word.md](docs/decisions/0002-what-counts-as-a-word.md)).
