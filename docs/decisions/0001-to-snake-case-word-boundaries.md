<!-- ADR 0001: how to_snake_case splits identifiers into words, runs of capitals included. -->
# 0001. Word boundaries in `to_snake_case`

Status: accepted (plan task T1.7). T1.8 (`to_camel_case`), T1.10 (shared tokenizer) and
T2.3 (`to_kebab_case`) build on it.

## Context

`textkit.cases.to_snake_case(name)` converts camelCase, PascalCase and kebab-case identifiers
to snake_case. Splitting at `-`, `_` and at a lower-to-upper change (`camelCase`) is
uncontroversial, but runs of capitals are ambiguous: `HTTPServer` could become `h_t_t_p_server`,
`httpserver` or `http_server`, and `parseURL2` could become `parse_url_2`, `parse_url2` or
`parse_ur_l2`. Digits raise the same question: do they start a word of their own?

Callers convert real identifiers (class names, API fields), where a run of capitals is almost
always an acronym, and where digits are almost always part of the word before them
(`base64`, `utf8`, `v2`).

## Decision

`to_snake_case` splits `name` into words with these rules, applied in this order, then
lower-cases the words and joins them with `_`:

1. **Acronym followed by a word:** in a run of two or more capitals followed by a lower-case
   letter, the last capital starts a new word: `HTTPServer` -> `HTTP` + `Server`,
   `XMLHttpRequest` -> `XML` + `Http` + `Request`.
2. **Lower-case or digit followed by a capital:** a capital that follows a lower-case letter or
   a digit starts a new word: `camelCase` -> `camel` + `Case`, `HTTP2Server` -> `HTTP2` +
   `Server`.
3. **Digits never start a word.** A digit stays attached to whatever comes before it, letter or
   capital: `parseURL2` -> `parse` + `URL2`, `base64Encode` -> `base64` + `Encode`.
4. **Separators:** `-` and `_` separate words; a run of them counts as one, and separators at
   the start or end are dropped (`__init__` -> `init`). Input that is already snake_case comes
   out unchanged.
5. **ASCII only:** boundaries are detected only between ASCII letters and digits. Any other
   character (spaces, punctuation, non-ASCII letters) is kept where it is and only lower-cased
   (`Ñandú` -> `ñandú`).

A run of capitals with nothing after it stays one word (`ABC` -> `abc`, `getX` -> `get_x`).
A capitalized word glued to an acronym with no lower-case letter in between cannot be told
apart and is read as the acronym rule says: `ABCdef` -> `ab_cdef`.

The implementation is two regular-expression substitutions (rules 1 and 2) followed by
collapsing the separators (rule 4); the regular expressions use ASCII classes (rule 5).

## Consequences

- Acronyms survive as one word, which round-trips the common cases (`http_server`,
  `parse_url2`, `io_error`) and matches what most style guides expect.
- `to_snake_case` is not invertible: `HTTPServer` and `HttpServer` both give `http_server`.
- `to_kebab_case` (T2.3) inherits every row of the table below with `_` replaced by `-`.
- T1.10 may route only the parts where T1.5's prose word rule splits the same way through
  `textkit._tokens.words`; camel-case boundaries (rules 1 to 3) are specific to identifiers.
- Non-ASCII identifiers are not split; supporting them would be a new decision.

## Table of cases

`tests/test_cases.py` (`ToSnakeCaseTest`) asserts every row.

| Input | Output | Rule |
|-------|--------|------|
| `"HTTPServer"` | `"http_server"` | 1 |
| `"parseURL2"` | `"parse_url2"` | 2, 3 |
| `"camelCase"` | `"camel_case"` | 2 |
| `"PascalCase"` | `"pascal_case"` | 2 |
| `"kebab-case"` | `"kebab_case"` | 4 |
| `"already_snake"` | `"already_snake"` | 4 |
| `""` | `""` | - |
| `"getHTTPResponseCode"` | `"get_http_response_code"` | 1, 2 |
| `"XMLHttpRequest"` | `"xml_http_request"` | 1, 2 |
| `"HTTP2Server"` | `"http2_server"` | 2, 3 |
| `"base64Encode"` | `"base64_encode"` | 2, 3 |
| `"IOError"` | `"io_error"` | 1 |
| `"getX"` | `"get_x"` | 2 |
| `"ABC"` | `"abc"` | - |
| `"ABCdef"` | `"ab_cdef"` | 1 |
| `"kebab--Case"` | `"kebab_case"` | 4 |
| `"snake_Case"` | `"snake_case"` | 4 |
| `"__init__"` | `"init"` | 4 |
| `"Ñandú"` | `"ñandú"` | 5 |
