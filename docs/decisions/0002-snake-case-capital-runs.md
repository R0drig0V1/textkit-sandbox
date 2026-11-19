<!-- ADR 0002: how to_snake_case splits runs of capitals, digits and separators. -->
# 0002. How `to_snake_case` splits runs of capitals

## Context

`textkit.cases.to_snake_case` (plan task T1.7) turns camelCase, PascalCase and kebab-case
identifiers into snake_case. "Insert `_` before every capital" breaks on acronyms:
`HTTPServer` would become `h_t_t_p_server`. Lower-casing whole runs of capitals instead
gives `httpserver`, losing the boundary. Digits (`parseURL2`, `HTTP2Server`) need a rule
too. T2.3 (`to_kebab_case`) is built on this function and T1.10 compares this rule with the
word rule of `word_count`, so the rule has to be pinned down, with cases that the tests
check row by row.

## Decision

1. **Separators.** `_` and `-` separate words. A run of them counts as one, and separators
   at either end are dropped (`-a--b-` -> `a_b`, `_private` -> `private`).
2. **Case boundaries.** Inside each separator-free chunk, a new word starts at an
   upper-case character when:
   - the character before it is lower-case or a digit (`camelCase` -> `camel|Case`,
     `HTTP2Server` -> `HTTP2|Server`); or
   - the character before it is upper-case and the character after it is lower-case: the
     last capital of a run starts the next word (`HTTPServer` -> `HTTP|Server`).
   So a run of capitals is one word (an acronym), minus its last letter when a lower-case
   letter follows that letter.
3. **Digits** never start a word: they stay with the word before them (`parseURL2` ->
   `parse_url2`, `ipv4Address` -> `ipv4_address`).
4. Every word is **lower-cased** and the words are joined with `_`.
5. **Other characters** (spaces, punctuation) are neither separators nor boundaries; they
   are kept as they are, lower-cased. They are outside the inputs the function is meant for.
6. Upper and lower case come from `str.isupper` / `str.islower`, so non-ASCII letters split
   the same way (`ÉcoleNormale` -> `école_normale`).
7. A non-`str` argument raises `TypeError`.

## Consequences

- Acronyms survive as one word: `getHTTPResponseCode` -> `get_http_response_code`,
  `IOError` -> `io_error`.
- The rule cannot tell an acronym followed by a lower-case plural from an acronym followed
  by a new word: `PDFs` -> `pd_fs`. Callers that need `pdfs` must write `Pdfs` or `PDFS`.
  The same limitation exists in the usual regex-based converters; fixing it would need a
  dictionary of words.
- Digits glued to the previous word mean `ipv4Address` reads naturally, but a leading
  number in a word is never split off (`version2beta` stays one word); only a capital after
  the digit starts a new word (`version2Beta` -> `version2_beta`).
- The conversion is not reversible: `already_snake`, `alreadySnake` and `already-snake` all
  give `already_snake`.
- `tests/test_cases.py` holds the table below as literals and also checks that this table
  and its literals stay identical, so a new row here fails the tests until it is tested.

## Cases

Inputs and outputs are Python string literals.

| Input | Output |
|-------|--------|
| `"HTTPServer"` | `"http_server"` |
| `"parseURL2"` | `"parse_url2"` |
| `"camelCase"` | `"camel_case"` |
| `"PascalCase"` | `"pascal_case"` |
| `"kebab-case"` | `"kebab_case"` |
| `"already_snake"` | `"already_snake"` |
| `""` | `""` |
| `"getHTTPResponseCode"` | `"get_http_response_code"` |
| `"IOError"` | `"io_error"` |
| `"HTTP2Server"` | `"http2_server"` |
| `"ABC"` | `"abc"` |
| `"A"` | `"a"` |
| `"ipv4Address"` | `"ipv4_address"` |
| `"version2Beta"` | `"version2_beta"` |
| `"PDFs"` | `"pd_fs"` |
| `"Already_Snake"` | `"already_snake"` |
| `"kebab--case"` | `"kebab_case"` |
| `"-leading-and-trailing-"` | `"leading_and_trailing"` |
| `"_private"` | `"private"` |
| `"mixed-kebab_snakeCase"` | `"mixed_kebab_snake_case"` |
| `"---"` | `""` |
| `"ÉcoleNormale"` | `"école_normale"` |
