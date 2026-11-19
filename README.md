# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `slug_title` | `textkit.strings` | Builds a slug of at most `max_len` characters that never ends in `-` |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case identifiers to snake_case |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0001) |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
