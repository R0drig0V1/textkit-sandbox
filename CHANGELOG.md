# Changelog

## Unreleased

- Added `char_freq` in `textkit.counts`: counts each character that is not `str.isspace()`, case-sensitive, keys in order of first occurrence.
- Added `human_bytes` in the new module `textkit.sizes`: formats a byte count in binary units B, KiB, MiB, GiB, TiB (`1536` -> `"1.5 KiB"`), the unit chosen before rounding; raises `ValueError` for a negative or non-`int` `n` (a `bool` included) or one too large for a float.
- Added `is_palindrome`: tells whether text reads the same backwards, ignoring case, spaces, punctuation and accents; digits count, and `""` or text with no letters or digits gives `True`.
- Added `reading_time`: whole minutes to read a text at `wpm` words per minute (default 200), rounded up, 0 for text with no words; raises `ValueError` when `wpm < 1` (rule: [docs/decisions/0004-reading-time-rounding.md](docs/decisions/0004-reading-time-rounding.md)).
- Added `sentence_count`: counts sentences; a run of `.`, `!`, `?` or `…` ends one sentence, while decimals such as `3.14`, abbreviations such as `e.g.` and `Dr.`, and an ellipsis before a lowercase word do not (rule: [docs/decisions/0005-sentence-boundaries.md](docs/decisions/0005-sentence-boundaries.md)).
- Added `slug_title`: a slug of at most `max_len` characters that never ends in `-` (character cut); raises `ValueError` when `max_len` is negative.
- Added `slugify`: turns text into a lower-case ASCII slug.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (`"Ñandú"` -> `"Nandu"`).
- Added `truncate`: shortens text to a width, ending with a suffix when cut; raises `ValueError` when the width is smaller than the suffix.
- Added `to_camel_case`: converts snake_case and kebab-case identifiers to camelCase; a run of `-`/`_` counts as one separator, and input with no separator only has its first character lower-cased.
- Added `to_kebab_case`: converts camelCase, PascalCase and snake_case identifiers to kebab-case, with the word boundaries of `to_snake_case` ([docs/decisions/0003-snake-case-capital-runs.md](docs/decisions/0003-snake-case-capital-runs.md)).
- Added `to_snake_case`: converts camelCase, PascalCase and kebab-case identifiers to snake_case ([ADR](docs/decisions/0003-snake-case-capital-runs.md)).
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are reflowed (ADR 0001).
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers such as `3.14` count as one (rule: [docs/decisions/0002-what-counts-as-a-word.md](docs/decisions/0002-what-counts-as-a-word.md)).
