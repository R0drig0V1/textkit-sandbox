# Changelog

## Unreleased

- Added `char_freq`: counts each non-whitespace character of a text (case-sensitive, keys in order of first occurrence).
- Added `human_bytes`: a byte count in binary units (B, KiB, MiB, GiB, TiB), exact below 1024 and with one decimal from KiB up.
- Added `initials`: the upper-cased first letter of each space- or hyphen-separated part of a name, with no separators.
- Added `render`: fills `{name}` placeholders from a mapping, with `{{`/`}}` escapes and no format specs.
- Added `levenshtein`: edit distance between two strings (insertions, deletions and substitutions of cost 1).
- Added `number_to_words`: writes a whole number from 0 to 999 in English words, lower case, hyphenated tens, no "and".
- Added `ordinal`: appends the English ordinal suffix to a non-negative integer (`1` -> `1st`, `11` -> `11th`, `1021` -> `1021st`).
- Added `parse_duration`: seconds in a duration made of optional `h`, `m` and `s` parts in that order (`1h30m` -> 5400); anything else raises `ValueError`.
- Added `pluralize`: English plural of a singular noun (rules in docs/decisions/0004-pluralize-rules.md).
- Added `reading_time`: whole minutes to read a text at `wpm` words per minute (default 200), from `word_count`, rounded up (docs/decisions/0006-reading-time-rounding.md).
- Added the `python3 -m textkit` command line.
- Added `sentence_count`: counts the sentences in a text; abbreviations, initials and mid-sentence ellipses do not end one (docs/decisions/0007-sentence-count-abbreviations-and-ellipses.md).
- Added `slug_title`: the slug of a text cut to at most `max_len` characters, never ending in `-`.
- Added `rot13`: rotates ASCII letters by 13 places keeping their case; its own inverse.
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
