# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).
[docs/usage.md](docs/usage.md) has a runnable example of every function (tested as doctests).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `center` | `textkit.strings` | Pads text on both sides to a width, the odd extra fill on the right |
| `apply_patch` | `textkit.diff` | Applies a unified diff to a text, at its stated lines (no fuzz); `PatchError` otherwise |
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive |
| `dedent` | `textkit.strings` | Removes the indentation of spaces and tabs common to every non-blank line |
| `diff_words` | `textkit.diff` | Word-by-word diff of two texts as `(op, word)` pairs |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, accents and symbols |
| `levenshtein` | `textkit.strings` | Edit distance between two strings, counted over code points |
| `ngrams` | `textkit.counts` | Runs of `n` consecutive words of a text, in order (words: ADR 0002) |
| `reading_time` | `textkit.counts` | Whole minutes to read a text, rounded up (ADR 0004) |
| `render` | `textkit.template` | Fills a template (`{{ x }}`, `if`, `for`, filters) from a dict; missing names: ADR 0008 |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text (abbreviations, ellipses: ADR 0005) |
| `slug_title` | `textkit.strings` | Slug cut to a maximum length, never ending in `-` |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents) from text |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix when cut |
| `unified_diff` | `textkit.diff` | Unified diff of two texts, as GNU `diff -u` (ADR 0007) |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0002) |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `python3 -m textkit <function> "<text>"`: prints the result of a public function that
  takes one text argument (found at run time; other parameters keep their defaults).
  `python3 -m textkit --help` lists them under `commands:`, then the tools under `tools:`.
  Lists and dicts print as JSON with sorted keys. Exit 0 on success, 2 on an unknown
  command or a wrong argument count, 1 when the function rejects the text
  (`textkit.errors.TextkitError`, ADR 0006; any other exception is a bug and keeps its
  traceback).
- Tools are subcommands with arguments of their own, one module each:
  `textkit/cli/<name>.py` registers a `Command` (`textkit/cli/registry.py`) and is found at
  run time, so adding a tool edits no shared file. A tool returns its own exit code. The
  tools follow, one bullet each, in alphabetical order of subcommand.
  - `python3 -m textkit diff <file-a> <file-b>`: prints the unified diff of two UTF-8 files
    (`unified_diff`, headers `--- a` and `+++ b`; read with no newline translation, so
    `"\r\n"` and `"\n"` lines differ). Exit 0 when they are equal (nothing printed), 1 when
    they differ, 2 when a file cannot be read or is not valid UTF-8. See
    [docs/diff.md](docs/diff.md).
- `python3 -m textkit render <template-file> <json-file>`: renders a template file
  ([docs/template.md](docs/template.md)) with the JSON object in the second file and writes
  the result as is. Exit 0 on success, 1 with `line:column: message` on stderr for a
  template error, 2 for a file that cannot be read, a JSON file that is not an object or
  holds a lone surrogate, or a result stdout cannot encode.
