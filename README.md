# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `slugify` | `textkit.strings` | Lower-case ASCII slug, runs of other characters become one `-` |
| `is_email` | `textkit.emails` | Tells whether a string is a syntactically valid e-mail address (offline) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
