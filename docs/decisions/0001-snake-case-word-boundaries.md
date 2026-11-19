<!-- ADR 0001: where to_snake_case (textkit/cases.py) splits words; its table is tested row by row. -->
# 0001. Word boundaries in `to_snake_case`

## Context

`to_snake_case(name)` (plan task T1.7, `textkit/cases.py`) converts camelCase, PascalCase and
kebab-case identifiers to snake_case. Splitting at every capital is not enough: identifiers
contain runs of capitals (acronyms such as `HTTPServer`) and digits (`parseURL2`), and each
choice there changes the output. `to_camel_case` (T1.8), the shared tokenizer (T1.10) and
`to_kebab_case` (T2.3, built on `to_snake_case`) depend on this rule, so it is fixed here.

## Decision

1. Every `-` becomes `_`. Existing `_` are kept as they are (not collapsed, not stripped), so
   snake_case input, leading underscores included, is only lower-cased.
2. In a run of capitals followed by a lower-case letter, the last capital starts a new word:
   the run before it is an acronym (`HTTPServer` -> `HTTP` + `Server`).
3. A capital that follows a lower-case letter or a digit starts a new word
   (`camelCase` -> `camel` + `Case`, `HTTP2Server` -> `HTTP2` + `Server`).
4. Digits never start a word: they stay with the word before them (`parseURL2` ->
   `parse_url2`, `utf8Encode` -> `utf8_encode`).
5. The words are joined with `_` and the result is lower-cased with `str.lower`.

Only ASCII letters (`A-Z`, `a-z`) take part in rules 2 and 3; any other character creates no
boundary and passes through, lower-cased. Steps 2 and 3 are two regular-expression
substitutions, in that order (`textkit/cases.py`).

Alternatives rejected:

- **Split at every capital** (`HTTPServer` -> `h_t_t_p_server`): unreadable for acronyms.
- **Treat a whole capital run as one word** (`HTTPServer` -> `httpserver`): loses the
  boundary that the lower-case letter after the run makes obvious.
- **Split letters from digits** (`parseURL2` -> `parse_url_2`): `utf8`, `base64`, `v2` are
  single words far more often than not, and splitting them makes the conversion lossy in the
  common case.

## Consequences

- The rule matches what most snake_case converters do for acronyms, so results look familiar.
- Plural or mixed-case acronyms split wrongly: `parseURLs` -> `parse_ur_ls`, because the `s`
  makes `L` look like the start of a word. Callers who care write `parseUrls`.
- Two-letter alternations are ambiguous and the rule picks one reading:
  `ABcDEf` -> `a_bc_d_ef`.
- The conversion is not reversible: `IOError` and `IoError` both give `io_error`.
- Whitespace and punctuation other than `-` and `_` are not separators; input is expected to
  be an identifier.

## Cases

Tested row by row in `tests/test_cases.py` (`ToSnakeCaseTest`).

| Input | Output |
|-------|--------|
| `HTTPServer` | `http_server` |
| `parseURL2` | `parse_url2` |
| `camelCase` | `camel_case` |
| `PascalCase` | `pascal_case` |
| `kebab-case` | `kebab_case` |
| `already_snake` | `already_snake` |
| `""` (empty) | `""` (empty) |
| `getHTTPResponse` | `get_http_response` |
| `HTTP2Server` | `http2_server` |
| `utf8Encode` | `utf8_encode` |
| `IOError` | `io_error` |
| `ABC` | `abc` |
| `SCREAMING_SNAKE` | `screaming_snake` |
| `my-HTTPServer` | `my_http_server` |
| `_private` | `_private` |
| `parseURLs` | `parse_ur_ls` |
