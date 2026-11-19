# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `slug_title` | `textkit.strings` | Builds a slug of at most `max_len` characters that never ends in `-` |
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `reading_time` | `textkit.counts` | Estimates whole minutes to read a text, rounded up (rule: ADR 0004) |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same both ways, ignoring case, spaces, punctuation and accents |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text, aware of abbreviations and ellipses (rule: ADR 0005) |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case identifiers to camelCase (`"user_id"` -> `"userId"`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case identifiers to kebab-case (`"HTTPServer"` -> `"http-server"`) |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case identifiers to snake_case |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0002) |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
