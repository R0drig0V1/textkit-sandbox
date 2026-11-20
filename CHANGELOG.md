# Changelog

## Unreleased

- Added `apply_patch` in the new package `textkit.diff`: applies a unified diff (GNU numbering) at the lines its hunks state, with no fuzz; raises `PatchError` (an `InvalidValueError`) for a malformed patch or one that does not apply.
- Added `center`: pads text on both sides with `fill` to `width` code points, the odd extra on the right (unlike `str.center`); a bad `fill` or a negative `width` raises `InvalidValueError`.
- Added `char_freq` in `textkit.counts`: counts each non-whitespace character, case-sensitive, keys in order of first occurrence.
- Added `diff_words` in `textkit.diff`: word-by-word differences as `("=" | "-" | "+", word)` pairs over the words of ADR 0002.
- Added `dedent`: removes the prefix of spaces and tabs common to every non-blank line (no `textwrap`); line endings, as `str.splitlines` finds them, are kept; blank lines become empty.
- Added `is_palindrome`: tells whether text reads the same backwards, ignoring case, accents and symbols.
- Added `ngrams` in `textkit.counts`: the runs of `n` consecutive words (default 2, words as in `word_count`, ADR 0002, kept exactly as written), in order; fewer than `n` words give `[]`; `n < 1` raises `InvalidValueError`.
- Added `reading_time` in `textkit.counts`: whole minutes to read a text at `wpm` words per minute (default 200), from `word_count` (ADR 0002), rounded up: empty text is 0, under one minute is 1 (ADR 0004); `wpm < 1` raises `InvalidValueError`.
- Added `render` in the new package `textkit.template`: a text template engine with `{{ name }}`, `{% if %}`, `{% for %}` (with `loop.index`), comments and a fixed table of filters; errors `TemplateError` and `TemplateSyntaxError` carry the line and column; a missing name is an error in output and `for`, false in `if` (ADR 0008); subcommand `python3 -m textkit render <template-file> <json-file>`.
- Added `sentence_count` in `textkit.counts`: counts sentences; listed abbreviations (`Dr.`, `e.g.`), initials and an end followed by lower case (ellipses included) do not end one (ADR 0005).
- Added `slug_title`: slug cut to a maximum length (character cut), never ending in `-`.
- Added the `python3 -m textkit` command line.
- Added `python3 -m textkit --version`.
- Added `slugify`: turns text into a lower-case ASCII slug (non-ASCII removed, no normalization).
- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `strip_accents`: removes combining marks (accents) from text.
- Added `to_camel_case`: converts snake_case or kebab-case identifiers to camelCase.
- Added `to_html` in the new package `textkit.markdown`: converts a Markdown subset (headings, paragraphs, lists, fenced code, quotes, rules, emphasis, code, links) to HTML; raw HTML is always escaped and links to schemes other than http, https and mailto become `#` (ADR 0009); and the subcommand `python3 -m textkit markdown <file>`.
- Added `to_kebab_case`: converts camelCase, PascalCase or snake_case identifiers to kebab-case, splitting words like `to_snake_case` (ADR 0001).
- Added `to_snake_case`: converts camelCase, PascalCase or kebab-case identifiers to snake_case.
- Added `truncate`: shortens text to a width, ending in a suffix when cut.
- Added `unified_diff` in `textkit.diff`: line differences in the unified format of GNU `diff -u`, with its own LCS (no `difflib`); a missing final newline, the tie rule and the cost in ADR 0007.
- Added `word_count` in the new module `textkit.counts`: counts words; hyphenated words, contractions and numbers count once (ADR 0002).
- Added `wrap`: splits text into lines of at most `width` characters at spaces; existing newlines are treated as spaces (ADR 0003).
- `_tokens.words` returns tokens with their offsets.
- Split the command line into `textkit/cli/`.
- Added `textkit.errors`: functions raise `InvalidValueError` instead of `ValueError`.
- Added the `python3 -m textkit diff <file-a> <file-b>` subcommand: exit 0 equal, 1 different, 2 unreadable file.
