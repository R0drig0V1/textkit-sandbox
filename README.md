# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `human_bytes` | `textkit.sizes` | Formats a byte count in binary units (`1536` -> `"1.5 KiB"`, up to TiB) |
| `initials` | `textkit.names` | Returns the upper-case initials of a name split on spaces and hyphens (`"jean-luc picard"` -> `"JLP"`) |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, spaces, punctuation and accents |
| `parse_duration` | `textkit.durations` | Parses a compact duration such as `"1h30m"` into whole seconds |
| `number_to_words` | `textkit.numwords` | Spells `0..999` in lower-case English words, hyphenated tens, no "and" (`42` -> `"forty-two"`) |
| `reading_time` | `textkit.counts` | Estimates the whole minutes needed to read a text (rounding: [0004-reading-time-rounding](docs/decisions/0004-reading-time-rounding.md)) |
| `render` | `textkit.templates` | Fills `{name}` placeholders from a mapping with `str()` only; `{{` and `}}` are literal braces |
| `sentence_count` | `textkit.counts` | Counts the sentences of a text (rule: [0005-sentence-boundaries](docs/decisions/0005-sentence-boundaries.md)) |
| `slug_title` | `textkit.strings` | Makes a slug of at most `max_len` characters that never ends in `-` |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`) |
| `soundex` | `textkit.phonetic` | Returns the American Soundex code of a name (`"Robert"` -> `"R163"`); H and W are transparent, non-letters are removed |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents, diacritics) |
| `truncate` | `textkit.strings` | Shortens text to a width, ending with a suffix when cut |
| `to_camel_case` | `textkit.cases` | Converts snake_case and kebab-case identifiers to camelCase (`"user_id"` -> `"userId"`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase and snake_case identifiers to kebab-case |
| `to_roman` | `textkit.roman` | Writes an integer from 1 to 3999 as a Roman numeral in subtractive form (`1994` -> `"MCMXCIV"`) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase and kebab-case identifiers to snake_case |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces |
| `word_count` | `textkit.counts` | Counts the words of a text (rule: [0002-what-counts-as-a-word](docs/decisions/0002-what-counts-as-a-word.md)) |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
