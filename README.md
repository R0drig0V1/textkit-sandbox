# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `render` | `textkit.templates` | Fills `{name}` placeholders from a mapping; `{{` and `}}` are literal braces |
| `levenshtein` | `textkit.distance` | Edit distance with insertions, deletions and substitutions of cost 1 |
| `pluralize` | `textkit.plural` | English plural of a singular noun, with a few irregulars |
| `slug_title` | `textkit.strings` | Slug cut to a maximum length, never ending in `-` |
| `slugify` | `textkit.strings` | Lower-case ASCII slug, runs of other characters become one `-` |
| `soundex` | `textkit.phonetic` | Returns the four-character American Soundex code of a name |
| `is_email` | `textkit.emails` | Tells whether a string is a syntactically valid e-mail address (offline) |
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
