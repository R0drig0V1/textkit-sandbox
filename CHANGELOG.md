# Changelog

## Unreleased

- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `slugify`: turns text into an ASCII lower-case slug joined by `-` (non-ASCII is dropped).
- Added `word_count` in the new module `textkit.counts`: counts words by the rule of ADR 0001.
- Added `truncate`: shortens text to exactly `width` characters, suffix included; raises `ValueError` when `width` is smaller than the suffix.
