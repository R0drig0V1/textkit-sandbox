# Changelog

## Unreleased

- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `truncate`: shortens text to a width, ending with a suffix when cut; raises `ValueError` when the width is smaller than the suffix.
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are reflowed (ADR 0001).
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers such as `3.14` count as one (rule: [docs/decisions/0002-what-counts-as-a-word.md](docs/decisions/0002-what-counts-as-a-word.md)).
