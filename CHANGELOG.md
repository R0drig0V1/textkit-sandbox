# Changelog

## Unreleased

- Added `squeeze`: collapses runs of whitespace into single spaces.
- Added `slugify`: turns text into an ASCII lower-case slug joined by `-` (non-ASCII is dropped).
- Added `word_count` in the new module `textkit.counts`: counts words by the rule of ADR 0001.
- Added `truncate`: shortens text to exactly `width` characters, suffix included; raises `ValueError` when `width` is smaller than the suffix.
- Added `to_snake_case` (new module `textkit.cases`): converts camelCase, PascalCase and kebab-case names to snake_case; acronyms stay whole (ADR 0002).
- Added `strip_accents`: removes combining marks (NFD, drop category Mn, recompose with NFC).
- Added `char_freq` in `textkit.counts`: counts each non-whitespace character (`str.isspace()`), case-sensitive, without normalising.
- Added `wrap`: splits text into lines of at most `width` characters at whitespace, keeping existing line breaks (ADR 0003).
- Added `slug_title`: a slug of at most `max_len` characters, cut at a `-` word boundary when possible (mid-word only if the first word alone is too long); `""` for an empty slug or `max_len == 0`; raises `ValueError` for a negative `max_len`.
- Added `to_camel_case` in `textkit.cases`: converts snake_case and kebab-case names to camelCase; words are split as in `to_snake_case` (ADR 0002), so PascalCase and acronyms are normalised (`"HTTPServer"` -> `"httpServer"`).
- Added `sentence_count` in `textkit.counts`: counts sentences by the rule of ADR 0004 (abbreviations, ellipses, decimals, quotes, CJK terminators).
- Added `is_palindrome`: compares text with its reverse after `strip_accents`, `casefold` and keeping only `str.isalnum()` characters (digits count); `True` for empty text or text with no letters or digits; raises `TypeError` for a non-`str`.
- Added `reading_time` in `textkit.counts`: whole minutes to read a text, `ceil(word_count / wpm)` with exact arithmetic; raises `ValueError` for a non-positive or non-finite `wpm` and `TypeError` for a `bool` or non-numeric `wpm` (ADR 0005).
- Added `to_kebab_case` in `textkit.cases`: converts camelCase, PascalCase and snake_case names to kebab-case; words are split as in `to_snake_case` (ADR 0002), joined with `-`.
- Added the command line `python3 -m textkit <function> <text>` (`textkit/__main__.py`): every public one-text function is a command, found at run time; `--help` lists them; `-` reads the text from stdin; exit codes 0, 1 (the function rejected the text) and 2 (usage error).
