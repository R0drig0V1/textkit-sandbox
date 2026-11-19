# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive, in order of first occurrence |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, accents and non-alphanumerics |
| `reading_time` | `textkit.counts` | Whole minutes to read a text at `wpm` words per minute, rounded up (ADR 0004) |
| `slug_title` | `textkit.strings` | Slug cut to a maximum length, never ending in `-` (`"Hello, World!"`, 8 -> `"hello-wo"`) |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug (`"Hello, World!"` -> `"hello-world"`) |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (`"Ñandú"` -> `"Nandu"`) |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase (`"user_id"` -> `"userId"`) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case (`"HTTPServer"` -> `"http-server"`) |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `truncate` | `textkit.strings` | Cuts text to a width, ending in a suffix (`...` by default) |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0002) |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters, breaking between words |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `python3 -m textkit <function> "<text>"`: prints the result of any public function that
  takes one text argument (other parameters keep their defaults); `python3 -m textkit --help`
  lists them with the first line of each docstring. The commands are discovered at run time.
  Strings print as is, numbers and booleans with `print()`, dicts and lists as JSON with
  sorted keys. Exit 0 on success, 2 on an unknown function or a wrong argument count (usage
  on stderr), 1 when the function rejects the text with `ValueError`.
  `python3 -m textkit --version` prints `textkit <version>` (from `textkit.__version__`) and
  exits 0.

  ```console
  $ python3 -m textkit slugify "Hello, World!"
  hello-world
  $ python3 -m textkit char_freq "banana"
  {"a": 3, "b": 1, "n": 2}
  $ python3 -m textkit --version
  textkit 0.1.0
  ```
