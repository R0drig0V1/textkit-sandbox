# Changelog

## Unreleased

- Added `render`: fills `{name}` placeholders from a mapping, with `{{`/`}}` escapes and no format specs.
- Added `slugify`: lower-case ASCII slug of a text, runs of other characters become one `-`.
- Added `soundex`: the four-character American Soundex code of a name.
- Added `is_email`: tells whether a string is a syntactically valid e-mail address, offline.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `truncate`: cuts text to a width, ending with a suffix when cut.
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case to kebab-case, with the same word rules as `to_snake_case` (ADR 0001).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case to snake_case, keeping acronyms whole (ADR 0001).
- Added `word_count`: counts the words in a text (hyphenated words, contractions and numbers count as one).
