<!-- ADR 0001: how to_snake_case splits a name into words, runs of capitals included. -->
# 0001: Word boundaries in `to_snake_case`

## Context

`to_snake_case(name)` (T1.7, `textkit/cases.py`) takes camelCase, PascalCase and kebab-case
names. Splitting `camelCase` is obvious; runs of capitals are not: `HTTPServer` could be
`h_t_t_p_server`, `httpserver` or `http_server`, and `parseURL2` raises the question of
where digits go. `to_camel_case` (T1.8), the shared tokenizer (T1.10) and `to_kebab_case`
(T2.3) build on this rule, so it is fixed here once.

## Decision

A name is cut into words, the words are lower-cased (`str.lower`) and joined with `_`.

1. **Separators.** `_` and `-` separate words. A run of them counts as one separator;
   leading and trailing runs are dropped, so `__init__` gives `init` (the same choice as
   T1.8 makes for `to_camel_case`). No other character is a separator.
2. **Lower to upper.** An upper-case character that follows a lower-case one starts a word:
   `camelCase` -> `camel`, `Case`.
3. **Runs of capitals.** A run of upper-case characters is one word (an acronym), except
   that when a lower-case character follows the run, the run's last capital starts the next
   word: `HTTPServer` -> `HTTP`, `Server`; `IOError` -> `IO`, `Error`. A run at the end of the
   name stays whole: `parseURL` -> `parse`, `URL`.
4. **Digits** never start a word; they stay with the word before them (`parseURL2` ->
   `parse`, `URL2`; `utf8` stays one word). An upper-case character after a digit starts a
   word (`HTTP2Server` -> `HTTP2`, `Server`; `utf8Decoder` -> `utf8`, `Decoder`).
5. **Case is Unicode-aware** (`str.isupper`, `str.islower`, `str.isdigit`), so
   `ÉcoleNormale` splits like `EcoleNormale`. Any other character (punctuation, spaces,
   characters without case) is kept inside its word and never starts one.

The function never raises for a `str`; `""` and separator-only input give `""`.

Rejected: one word per capital (`h_t_t_p_server`) loses the acronym; never splitting a run
(`httpserver`) loses the word boundary every reader sees; splitting before digits
(`parse_url_2`) breaks names like `utf8` and `sha256` into meaningless pieces.

## Consequences

- snake_case input comes back unchanged, and `to_snake_case` is idempotent.
- The conversion is lossy: `HTTPServer` and `HttpServer` both give `http_server`, and
  `_private` loses its leading underscore. Round trips through `to_camel_case` are not
  guaranteed.
- `to_kebab_case` (T2.3) can reuse the same words and join them with `-`.
- T1.10 can route through the shared tokenizer only the rows below whose split agrees with
  T1.5's word rule; case boundaries (rules 2-4) are specific to identifiers.

## Cases

Tested row by row in `tests/test_cases.py` (`CASES`, same order).

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
| `IOError` | `io_error` |
| `HTTP2Server` | `http2_server` |
| `utf8Decoder` | `utf8_decoder` |
| `ABC` | `abc` |
| `SCREAMING_SNAKE` | `screaming_snake` |
| `mixed-Kebab_snakeCase` | `mixed_kebab_snake_case` |
| `__private--name__` | `private_name` |
| `--` | `""` |
| `ÉcoleNormale` | `école_normale` |
