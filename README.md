# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `slugify` | `textkit.strings` | Turns text into an ASCII lower-case slug joined by `-` |
| `word_count` | `textkit.counts` | Counts words: hyphenated words, contractions and numbers count once, any script ([ADR 0001](docs/decisions/0001-what-counts-as-a-word.md)) |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix (`...` by default) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase and kebab-case names to snake_case (ADR 0002) |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
