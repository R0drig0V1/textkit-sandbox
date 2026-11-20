# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix when cut |
| `word_count` | `textkit.counts` | Counts the words in a text, by the rule of ADR 0001 |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
