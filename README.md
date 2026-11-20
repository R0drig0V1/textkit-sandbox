# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).
[docs/usage.md](docs/usage.md) has a runnable example of every function (tested as doctests).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, accents and symbols |
| `ngrams` | `textkit.counts` | Runs of `n` consecutive words of a text, in order (words: ADR 0002) |
| `reading_time` | `textkit.counts` | Whole minutes to read a text, rounded up (ADR 0004) |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text (abbreviations, ellipses: ADR 0005) |
| `slug_title` | `textkit.strings` | Slug cut to a maximum length, never ending in `-` |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents) from text |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix when cut |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0002) |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `python3 -m textkit <function> "<text>"`: prints the result of a public function that
  takes one text argument (found at run time; other parameters keep their defaults).
  `python3 -m textkit --help` lists them under `commands:`, then the tools under `tools:`.
  Lists and dicts print as JSON with sorted keys. Exit 0 on success, 2 on an unknown
  command or a wrong argument count, 1 when the function rejects the text (`ValueError`).
- Tools are subcommands with arguments of their own, one module each:
  `textkit/cli/<name>.py` registers a `Command` (`textkit/cli/registry.py`) and is found at
  run time, so adding a tool edits no shared file. A tool returns its own exit code. The
  tools follow, one bullet each, in alphabetical order of subcommand.
