# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `slug_title` | `textkit.strings` | Slug cut to at most a length, never ending in `-` (`"Hello, World!"`, 8 -> `hello-wo`) |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `hello-world`) |
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive |
| `reading_time` | `textkit.counts` | Minutes to read a text at a words-per-minute rate, rounded up (ADR "Reading time rounding") |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text, handling abbreviations and ellipses (ADR "Sentence boundaries: abbreviations and ellipses") |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase (`"user_id"` -> `"userId"`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case (`"HTTPServer"` -> `"http-server"`) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `truncate` | `textkit.strings` | Shortens text to a width, suffix included |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR "What counts as a word") |
| `wrap` | `textkit.strings` | Splits text into lines of at most a width, at spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `python3 -m textkit <function> "<text>"`: runs any public function of one text
  argument and prints the result (`dict`/`list` as JSON); `python3 -m textkit --help` lists
  them. Exit 0 on success, 2 on an unknown function or a wrong argument count.
