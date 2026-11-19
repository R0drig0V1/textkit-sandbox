# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, accents, spaces and punctuation |
| `slug_title` | `textkit.strings` | Slug of at most `max_len` characters that never ends in `-` |
| `reading_time` | `textkit.counts` | Whole minutes to read a text at `wpm` words per minute, rounded up (ADR 0004) |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text, with abbreviations and ellipses handled (ADR 0005) |
| `slugify` | `textkit.strings` | Lower-cases text into an ASCII slug joined by `-` |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case identifiers to camelCase |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case identifiers to kebab-case |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case identifiers to snake_case |
| `word_count` | `textkit.counts` | Counts the words in a text (rule in ADR 0002) |
| `truncate` | `textkit.strings` | Shortens text to a width, ending with a suffix when cut |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `python3 -m textkit <function> "<text>"`: runs any function of the table that takes one
  text argument and prints the result (`dict` and `list` as JSON); `python3 -m textkit
  --help` lists them.
- `python3 -m textkit --version`: prints `textkit <version>` (`textkit.__version__`).
