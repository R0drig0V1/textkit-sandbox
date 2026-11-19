<!-- ADR 0001: how to_snake_case splits runs of capitals, digits and separators. -->
# 0001. Splitting runs of capitals in `to_snake_case`

## Context

`textkit.cases.to_snake_case` (plan task T1.7) converts camelCase, PascalCase and kebab-case
identifiers to snake_case. Splitting at every capital is wrong for acronyms: `HTTPServer`
would become `h_t_t_p_server`. Not splitting runs at all is also wrong: `HTTPServer` would
become `httpserver`. Digits need a rule too (`parseURL2`, `URL2Parser`). Later tasks build on
this: T1.8 (`to_camel_case`) shares the module and T1.10 reuses the shared tokenizer where
its word rule and this one agree, so the rule has to be stated precisely.

## Decision

A word boundary is placed, using ASCII letters only:

1. **Before the last capital of a run of capitals that is followed by a lower-case letter.**
   The run is an acronym and the last capital starts the next word: `HTTPServer` ->
   `HTTP` + `Server`. A run of capitals with no lower-case letter after it stays one word:
   `parseURL` -> `parse` + `URL`, `HTTP` -> `HTTP`.
2. **Before a capital that follows a lower-case letter or a digit**: `camelCase` ->
   `camel` + `Case`, `URL2Parser` -> `URL2` + `Parser`.
3. **Digits never start a word**: they stay attached to whatever precedes them
   (`parseURL2` -> `parse` + `URL2`, `version2Beta` -> `version2` + `Beta`).

Separators: `-` and `_` both separate words; a run of them (`--`, `-_`) becomes one `_`, and
separators at either end are dropped. The result is lower-cased with `str.lower`. Input that
is already snake_case is unchanged, and the function is idempotent. Other characters
(spaces, punctuation, non-ASCII letters) are not boundaries and are kept, apart from
lower-casing; such input is outside the function's contract.

The implementation is two regular expressions applied in order (rule 1, then rules 2 and 3),
then the separator collapse and `lower()`.

## Consequences

- Acronyms survive as one word, which is what readers of `http_server` and `parse_url2`
  expect. The price: two adjacent acronyms cannot be told apart (`XMLHTTPRequest` ->
  `xmlhttp_request`), since no rule can know where one ends.
- Converting back with `to_camel_case` is lossy: `http_server` gives `httpServer`, not
  `HTTPServer`.
- Dropping leading and trailing separators means `_private` -> `private`; callers who need a
  leading underscore must keep it themselves.

## Cases

Every row is tested in `tests/test_cases.py` (`ToSnakeCaseTest.ADR_TABLE`).

| Input | Output |
|-------|--------|
| `HTTPServer` | `http_server` |
| `parseURL2` | `parse_url2` |
| `camelCase` | `camel_case` |
| `PascalCase` | `pascal_case` |
| `kebab-case` | `kebab_case` |
| `already_snake` | `already_snake` |
| `""` | `""` |
| `getHTTPResponseCode` | `get_http_response_code` |
| `URL2Parser` | `url2_parser` |
| `version2Beta` | `version2_beta` |
| `HTTP` | `http` |
| `A` | `a` |
| `Already_Snake` | `already_snake` |
| `kebab--case` | `kebab_case` |
| `-leading-and-trailing-` | `leading_and_trailing` |
| `mixed-kebab_snakeCase` | `mixed_kebab_snake_case` |
