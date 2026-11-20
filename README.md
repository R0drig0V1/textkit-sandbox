# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `reading_time` | `textkit.counts` | Whole minutes to read a text at `wpm` words per minute, rounded up (ADR 0004) |
| `slug_title` | `textkit.strings` | Makes a slug of at most `max_len` characters that never ends in `-` |
| `slugify` | `textkit.strings` | Makes a lower-case ASCII slug (`Hello, World!` -> `hello-world`) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case names to camelCase (`user_id` -> `userId`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case names to kebab-case (`HTTPServer` -> `http-server`) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case names to snake_case |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix when cut |
| `word_count` | `textkit.counts` | Counts the words in a text, by the rule of ADR 0002 |
| `wrap` | `textkit.strings` | Splits text into lines of at most a width, at whitespace |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `tests/test_api.py` (run by the unit tests) is the API contract: every public function has a
  docstring and type hints for all parameters and the return value, and the functions it
  discovers are exactly this table's rows, module included.
