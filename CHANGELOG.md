# Changelog

## Unreleased

- Added `char_freq` in `textkit.counts`: counts each non-whitespace character, case-sensitive, keys in order of first occurrence.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `truncate`: shortens text to a width, suffix included.
- Added `word_count` in the new module `textkit.counts`: counts words, keeping hyphenated words, contractions and numbers such as `3.14` whole (ADR "What counts as a word").
