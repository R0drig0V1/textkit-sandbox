# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh` and by
`tests/test_api.py`, which also requires a docstring and type hints on each).

| Function | Module | What it does |
|----------|--------|--------------|
| `reading_time` | `textkit.counts` | Whole minutes to read a text at `wpm` words per minute, rounded up (ADR 0004) |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text (abbreviations and ellipses: ADR 0005) |
| `slug_title` | `textkit.strings` | Slug cut to at most `max_len` characters, never ending in `-` |
| `slugify` | `textkit.strings` | Lower-case ASCII slug with runs of other characters turned into `-` |
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `is_palindrome` | `textkit.strings` | Tells whether a text is a palindrome, ignoring case, spaces, punctuation and accents |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase (`"user_id"` -> `"userId"`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case (`"HTTPServer"` -> `"http-server"`) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `truncate` | `textkit.strings` | Cuts text to a width, suffix included; returns it unchanged if it fits |
| `word_count` | `textkit.counts` | Counts the words in a text (word rule: ADR 0001) |
| `wrap` | `textkit.strings` | Splits text into lines of at most a width, at spaces; reflows existing newlines |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
