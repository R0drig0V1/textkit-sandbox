# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents), as in `"Ñandú"` -> `"Nandu"` |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case names to snake_case |
| `truncate` | `textkit.strings` | Cuts text to a width, ending in a suffix (`...` by default) |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0001) |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
