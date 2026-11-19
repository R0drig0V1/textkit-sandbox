# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `reading_time` | `textkit.counts` | Estimates reading time in whole minutes, rounded up (`wpm=200`; rule: ADR 0004) |
| `slug_title` | `textkit.strings` | Slug of text cut to at most `max_len` characters, never ending in `-` (`("Hello, World!", 8)` -> `"hello-wo"`) |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents) from text |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase (`"user_id"` -> `"userId"`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case (`"HTTPServer"` -> `"http-server"`, ADR 0002) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case (ADR 0002) |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix when cut |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0001) |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces, reflowing newlines (ADR 0003) |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
