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
| `to_camel_case` | `textkit.cases` | Converts snake_case and kebab-case names to camelCase (`"user_id"` -> `"userId"`), splitting as `to_snake_case` does |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, no Unicode normalisation |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters, keeping line breaks |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
