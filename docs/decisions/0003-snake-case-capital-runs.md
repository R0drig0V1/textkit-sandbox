<!-- ADR: how to_snake_case (textkit/cases.py) splits runs of capitals, digits and separators. -->
# 0003. How `to_snake_case` splits runs of capitals

## Context

`to_snake_case(name)` (plan task T1.7) converts camelCase, PascalCase and kebab-case
identifiers to snake_case. Splitting at every capital is unambiguous for `camelCase`, but
identifiers often contain acronyms (`HTTPServer`, `parseURL2`), where splitting at every
capital gives `h_t_t_p_server`, and digits, which could belong to either neighbour. A rule is
needed that readers can predict and that T1.10 can compare with the word rule of T1.5.

## Decision

1. **A run of capitals is one word.** Inside a run of capitals followed by a lower-case
   letter, the last capital starts the next word: `HTTPServer` -> `http_server`,
   `getHTTPResponseCode` -> `get_http_response_code`. A run at the end stays whole:
   `parseURL` -> `parse_url`, `ABC` -> `abc`.
2. **A capital after a lower-case letter or a digit starts a word**: `camelCase` ->
   `camel_case`, `HTTP2Server` -> `http2_server`, `version2Beta` -> `version2_beta`.
3. **Digits stay with the word before them**; a digit never starts a word by itself:
   `parseURL2` -> `parse_url2`, `utf8string` -> `utf8string`.
4. **Separators**: `-` and `_` are word separators; a run of them becomes one `_`, and
   separators at either end are dropped (`-leading_and_trailing-` -> `leading_and_trailing`).
   So kebab-case and snake_case input, `SCREAMING_SNAKE` included, convert directly.
5. The result is lower-cased.
6. **ASCII only for boundaries**: rules 1 and 2 look at `[A-Z]`, `[a-z]` and `[0-9]` only.
   Other characters are lower-cased and kept, but never create a boundary.

Implemented as two regular-expression substitutions (rule 1, then rule 2), then rule 4, then
rule 5.

## Consequences

- Acronyms survive as one word, which is what most style guides (PEP 8 among them) expect from
  a name like `HTTPServer`.
- A one-letter word before a capitalised word is indistinguishable from an acronym, and the
  rule treats it as a word: `iPhone` -> `i_phone`, `ABCd` -> `ab_cd`. Acceptable for
  identifiers; callers with such names should pass snake_case.
- A letter-digit boundary is never split, so `HTTP2` stays `http2` and the conversion is not
  reversible when the original split a word before a digit.
- Non-ASCII identifiers are not split: `ÉtéCase` -> `étécase`. Supporting them would need
  Unicode categories instead of ASCII classes; left out until a task asks for it.
- The function is idempotent: snake_case output converts to itself.
- Leading and trailing underscores are lost (`__init__` -> `init`); private or dunder names
  are not preserved.
- For T1.10: T1.5's word rule splits prose, not identifiers, so it will not see the capital
  boundaries of rules 1-2. It can at most match rule 4 (separators) for some rows.

## Case table

`tests/test_cases.py` (`ToSnakeCaseTest`) tests every row, in this order.

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
| `HTTP2Server` | `http2_server` |
| `version2Beta` | `version2_beta` |
| `ABC` | `abc` |
| `iPhone` | `i_phone` |
| `SCREAMING_SNAKE` | `screaming_snake` |
| `HTTP_server` | `http_server` |
| `kebab--snake__mixed-_case` | `kebab_snake_mixed_case` |
| `-leading_and_trailing-` | `leading_and_trailing` |
| `utf8string` | `utf8string` |
| `ÉtéCase` | `étécase` |
