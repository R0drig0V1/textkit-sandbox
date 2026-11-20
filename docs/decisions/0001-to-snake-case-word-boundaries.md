<!-- ADR 0001: where to_snake_case splits an identifier into words. -->
# 0001. Word boundaries in `to_snake_case`: runs of capitals and digits

Status: accepted (plan task T1.7)

## Context

`textkit.cases.to_snake_case` turns camelCase, PascalCase and kebab-case identifiers into
snake_case. Splitting at "every capital" is wrong for acronyms (`HTTPServer` would give
`h_t_t_p_server`), and keeping a whole run of capitals together is wrong when the run ends in
the first letter of the next word (`HTTPServer` would give `httpserver`). Digits need a rule
too (`parseURL2`, `URL2Path`, `utf8Encode`). The rule must be simple enough to state in a
docstring and to test row by row; T1.10 later compares it with the prose word rule of T1.5.

## Decision

The identifier is split into words; the words are lower-cased and joined with `_`.

1. **Separators.** Every run of characters that are not alphanumeric (`str.isalnum`: `-`,
   `_`, spaces, dots, ...) ends the current word and is dropped. A run counts as one
   separator; separators at either end produce no empty words. This is broader than the
   `-` and `_` the task names, so stray spaces or dots never leak into the output.
2. **Lower to upper.** An upper-case letter starts a new word when the character before it
   is not upper-case (a lower-case letter, a digit or a caseless letter): `camelCase` ->
   `camel` + `Case`, `URL2Path` -> `URL2` + `Path`.
3. **Runs of capitals.** Inside a run of capitals, the last capital starts a new word only
   when a lower-case letter follows it: `HTTPServer` -> `HTTP` + `Server`. A run that ends
   the name or is followed by a digit or separator stays whole: `ABC` -> `abc`.
4. **Digits** never start a word and never end one: they stay with the word before them
   (`parseURL2` -> `parse_url2`, `utf8Encode` -> `utf8_encode`). Only the letter after them
   can start a new word, by rule 2.

Letters are classified with `str.isupper` and `str.islower`, so non-ASCII letters follow the
same rules (`ÉtéChaud` -> `été_chaud`).

## Consequences

- Acronyms are preserved as one word in the common cases (`HTTPServer`, `IOError`,
  `getHTTPResponseCode`).
- A plural acronym is split wrongly: `PDFs` -> `pd_fs`, because rule 3 cannot tell a plural
  `s` from the start of a word. Callers who need `pdfs` must pre-process; recognising
  plurals would need a dictionary and is out of scope.
- A digit glued to the end of a word cannot be separated (`parseURL2` gives `parse_url2`,
  never `parse_url_2`). This matches the usual convention of tools such as `inflection`.
- `to_snake_case` is not a round trip with `to_camel_case` (T1.8): `HTTPServer` ->
  `http_server` -> `httpServer`.
- Leading underscores (`_private`) are dropped like any other separator.

## Table of cases

Tested row by row in `tests/test_cases.py` (`ADR_CASES`, same order).

| Input | Output | Rule |
|-------|--------|------|
| `HTTPServer` | `http_server` | 3 |
| `parseURL2` | `parse_url2` | 2, 4 |
| `camelCase` | `camel_case` | 2 |
| `PascalCase` | `pascal_case` | 2 |
| `kebab-case` | `kebab_case` | 1 |
| `already_snake` | `already_snake` | 1 |
| `""` (empty) | `""` (empty) | - |
| `getHTTPResponseCode` | `get_http_response_code` | 2, 3 |
| `URL2Path` | `url2_path` | 2, 4 |
| `utf8Encode` | `utf8_encode` | 2, 4 |
| `IOError` | `io_error` | 3 |
| `ABC` | `abc` | 3 |
| `A` | `a` | - |
| `SCREAMING_SNAKE` | `screaming_snake` | 1, 3 |
| `mixed-kebab_snake` | `mixed_kebab_snake` | 1 |
| `--leading--trailing--` | `leading_trailing` | 1 |
| `hello world` | `hello_world` | 1 |
| `PDFs` | `pd_fs` | 3 (known limitation) |
| `ÉtéChaud` | `été_chaud` | 2 |
