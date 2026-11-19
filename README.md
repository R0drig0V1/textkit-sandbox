# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `render` | `textkit.templates` | Fills `{name}` placeholders from a mapping; `{{` and `}}` are literal braces |
| `slugify` | `textkit.strings` | Lower-case ASCII slug, runs of other characters become one `-` |
| `soundex` | `textkit.phonetic` | Returns the four-character American Soundex code of a name |
| `is_email` | `textkit.emails` | Tells whether a string is a syntactically valid e-mail address (offline) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `truncate` | `textkit.strings` | Cuts text to a width, ending with a suffix when cut |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `word_count` | `textkit.counts` | Counts the words in a text |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
