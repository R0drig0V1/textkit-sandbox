# textkit-sandbox

Public, throwaway repository for testing the herdr-agent-pool workflow with real agents on a
tiny synthetic project. Nothing here matters; it can be wiped at any time.

`textkit` is a small Python package of text helpers (standard library only, Python 3.9+).
[docs/usage.md](docs/usage.md) has a runnable example of every function (tested as doctests).

## Functions

Every public function is listed here, once (checked by `scripts/check.sh`).

| Function | Module | What it does |
|----------|--------|--------------|
| `apply_patch` | `textkit.diff` | Applies a unified diff to a text, exactly where its hunks say (no fuzz) |
| `char_freq` | `textkit.counts` | Counts each non-whitespace character, case-sensitive |
| `diff_words` | `textkit.diff` | Word-by-word differences of two texts as `(op, word)` pairs |
| `is_palindrome` | `textkit.strings` | Tells whether text reads the same backwards, ignoring case, accents and symbols |
| `ngrams` | `textkit.counts` | Runs of `n` consecutive words of a text, in order (rule: ADR 0002) |
| `reading_time` | `textkit.counts` | Whole minutes to read a text, rounded up (ADR 0004) |
| `render` | `textkit.template` | Fills a text template (`{{ name }}`, `if`, `for`, filters) from a dict (missing names: ADR 0008) |
| `sentence_count` | `textkit.counts` | Counts the sentences in a text (abbreviations, ellipses: ADR 0005) |
| `slug_title` | `textkit.strings` | Slug cut to a maximum length, never ending in `-` |
| `slugify` | `textkit.strings` | Turns text into a lower-case ASCII slug |
| `squeeze` | `textkit.strings` | Collapses runs of whitespace into single spaces |
| `strip_accents` | `textkit.strings` | Removes combining marks (accents) from text |
| `to_camel_case` | `textkit.cases` | Converts snake_case or kebab-case to camelCase |
| `to_html` | `textkit.markdown` | Converts a safe Markdown subset to HTML: raw HTML escaped, unsafe link schemes dropped (ADR 0009) |
| `to_kebab_case` | `textkit.cases` | Converts camelCase, PascalCase or snake_case to kebab-case |
| `to_snake_case` | `textkit.cases` | Converts camelCase, PascalCase or kebab-case to snake_case |
| `truncate` | `textkit.strings` | Shortens text to a width, ending in a suffix when cut |
| `unified_diff` | `textkit.diff` | Line differences of two texts in the unified format of GNU `diff -u` (ADR 0007) |
| `word_count` | `textkit.counts` | Counts the words in a text (rule: ADR 0002) |
| `wrap` | `textkit.strings` | Splits text into lines of at most `width` characters at spaces |

## Commands

- `scripts/check.sh`: unit tests, this table, the changelog, ADR numbering.
- `python3 -m textkit <function> "<text>"`: prints the result of a public function that
  takes one text argument (found at run time; other parameters keep their defaults).
  `python3 -m textkit --help` lists them under `commands:`, then the tool subcommands under
  `tools:`. Lists and dicts print as JSON with sorted keys. Exit 0 on success, 2 on an
  unknown command or a wrong argument count, 1 when the function rejects the text (a
  `TextkitError` from `textkit.errors`, message on stderr, no traceback). Any other
  exception is a bug and keeps its traceback (ADR 0006).
- Tool subcommands, `python3 -m textkit <tool> ...`: one module `textkit/cli/<name>.py` each
  ([docs/usage.md](docs/usage.md#command-line)), and one bullet each below, in alphabetical
  order of subcommand.
- `python3 -m textkit diff <file-a> <file-b>`: prints `unified_diff` of the two files
  (headers `--- a` and `+++ b`; read as UTF-8, `"\r"` kept). Exit 0 when they are equal
  (nothing printed), 1 when they differ, 2 when a file cannot be read
  ([docs/diff.md](docs/diff.md)).
- `python3 -m textkit render <template-file> <json-file>`: renders a template
  (`textkit.template.render`, [docs/template.md](docs/template.md)) with the JSON object in
  the second file as its context and writes the result unchanged. Exit 0 on success, 1 for a
  template error (`line:column: message` on stderr), 2 for a file that cannot be read or a
  JSON file that is not a JSON object.
- `python3 -m textkit markdown <file>`: writes the HTML of a UTF-8 Markdown file
  (`to_html`, [docs/markdown.md](docs/markdown.md)). Exit 0, or 2 when the file is missing,
  unreadable or not valid UTF-8.
