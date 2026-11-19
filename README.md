# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `initials` | `textkit.names` | Upper-cased first letter of each space- or hyphen-separated part of a name |
| `render` | `textkit.templates` | Fills `{name}` placeholders from a mapping; `{{` and `}}` are literal braces |
| `levenshtein` | `textkit.distance` | Edit distance with insertions, deletions and substitutions of cost 1 |
| `number_to_words` | `textkit.numwords` | Writes a whole number from 0 to 999 in English words (`42` -> `forty-two`) |
| `ordinal` | `textkit.ordinals` | Appends the English ordinal suffix to a non-negative integer (`21` -> `21st`) |
| `pluralize` | `textkit.plural` | English plural of a singular noun, with a few irregulars |
| `reading_time` | `textkit.counts` | Whole minutes to read a text at `wpm` words per minute, rounded up |
| `slug_title` | `textkit.strings` | Slug cut to a maximum length, never ending in `-` |
| `slugify` | `textkit.strings` | Lower-case ASCII slug, runs of other characters become one `-` |
| `soundex` | `textkit.phonetic` | Returns the four-character American Soundex code of a name |
| `is_email` | `textkit.emails` | Tells whether a string is a syntactically valid e-mail address (offline) |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, punctuation and accents |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents) from text |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase |
| `truncate` | `textkit.strings` | Cuts text to a width, ending with a suffix when cut |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case |
| `to_roman` | `textkit.roman` | Converts an integer from 1 to 3999 to an upper-case Roman numeral |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `word_count` | `textkit.counts` | Counts the words in a text |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at whitespace |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
