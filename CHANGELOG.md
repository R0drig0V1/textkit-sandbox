# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character of a text (case-sensitive, keys in order of first occurrence).
- Added `render`: fills `{name}` placeholders from a mapping, with `{{`/`}}` escapes and no format specs.
- Added `levenshtein`: edit distance between two strings (insertions, deletions and substitutions of cost 1).
- Added `pluralize`: English plural of a singular noun (rules in docs/decisions/0004-pluralize-rules.md).
- Added `slug_title`: the slug of a text cut to at most `max_len` characters, never ending in `-`.
- Added `slugify`: lower-case ASCII slug of a text, runs of other characters become one `-`.
- Added `soundex`: the four-character American Soundex code of a name.
- Added `is_email`: tells whether a string is a syntactically valid e-mail address, offline.
- Added `is_palindrome`: tells whether text reads the same backwards, ignoring case, spaces, punctuation and accents.
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (accents) from text.
- Added `to_camel_case`: converts snake_case or kebab-case to camelCase; input with no separator only has its first character lower-cased.
- Added `truncate`: cuts text to a width, ending with a suffix when cut.
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case to kebab-case, with the same word rules as `to_snake_case` (ADR 0001).
- Added `to_roman`: converts an integer from 1 to 3999 to a Roman numeral in standard subtractive form (`1994` -> `MCMXCIV`).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case to snake_case, keeping acronyms whole (ADR 0001).
- Added `word_count`: counts the words in a text (hyphenated words, contractions and numbers count as one).
- Added `wrap`: splits text into lines of at most `width` characters at whitespace; existing newlines are reflowed (docs/decisions/0005-wrap-existing-newlines.md).
