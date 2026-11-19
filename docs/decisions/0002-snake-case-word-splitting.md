<!-- ADR 0002: how to_snake_case splits identifiers into words (plan task T1.7). -->
# 0002. Word splitting in `to_snake_case`: runs of capitals, digits and separators

Status: accepted (T1.7)

## Context

`to_snake_case(name)` in `textkit/cases.py` converts camelCase, PascalCase and kebab-case
identifiers to snake_case. Splitting at every capital is wrong for acronyms: `HTTPServer` would
become `h_t_t_p_server`. Digits are ambiguous too: `parseURL2` could be `parse_url2`,
`parse_url_2` or `parse_ur_l2`. Later tasks depend on the choice: T1.8 (`to_camel_case`, the
reverse direction) and T1.10 (the shared tokenizer, which may take over the parts of this rule
that agree with the word rule of ADR 0001), and phase 2 (T2.3).

Options considered for runs of capitals:

1. **Split at every capital** (`HTTPServer` -> `h_t_t_p_server`). Simple, unreadable.
2. **Keep a run of capitals as one word, and hand its last capital to the next word when a
   lower-case letter follows** (`HTTPServer` -> `http_server`, `getHTTPResponse` ->
   `get_http_response`). The rule of Rails' `underscore` and Python's `inflection`, so it
   matches what readers expect.
3. **Keep the whole run as one word** (`HTTPServer` -> `httpserver`). Loses a boundary that is
   obvious to a human reader.

Options for digits: a word boundary on both sides of a digit run (`parse_url_2`), or none
(`parse_url2`).

## Decision

Option 2, with digits treated like lower-case letters. `to_snake_case` splits the name into
words with these rules, applied in order, then lower-cases the words and joins them with `_`:

1. **Separators.** `-` and `_` separate words; a run of them counts as one, and leading and
   trailing separators are dropped (the same separator rule as T1.8's `to_camel_case`).
2. **End of an acronym.** In a run of two or more capitals followed by a lower-case letter, the
   last capital starts a new word: `HTTPServer` -> `HTTP` + `Server`.
3. **Lower to upper.** A capital that follows a lower-case letter or a digit starts a new word:
   `camelCase` -> `camel` + `Case`, `Version2Beta` -> `Version2` + `Beta`.

Digits never start a word: they stay with whatever precedes them (`parseURL2` ->
`parse_url2`, `HTTP2Server` -> `http2_server`, `base64Encode` -> `base64_encode`). Names like
`md5`, `utf8`, `base64` and `http2` are written as one word in practice, and keeping them whole
makes the conversion of `snake_case` names that contain them a no-op.

Only the ASCII capitals `A`-`Z` and lower-case letters `a`-`z` take part in rules 2 and 3.
Every other character (non-ASCII letters, spaces, punctuation) is kept, only lower-cased, and
never marks a boundary: the function converts identifiers, not prose.

## Consequences

- snake_case and SCREAMING_SNAKE_CASE input come back as snake_case unchanged in their words
  (`already_snake` -> `already_snake`, `SCREAMING_SNAKE` -> `screaming_snake`).
- Two-letter mixed-case brand names split: `iOS` -> `i_os`. Accepted; callers who care can
  special-case them.
- The conversion is lossy: `HTTPServer` and `HttpServer` both give `http_server`, so
  `to_camel_case(to_snake_case(x))` is not always `x`.
- Leading underscores are dropped (`_private` -> `private`, `__dunder__` -> `dunder`): Python's
  private and dunder markers do not survive. Accepted for symmetry with `to_camel_case`.
- Spaces are not separators: `"hello world"` -> `"hello world"`. If phrases are ever supported
  it is a new decision, not a silent change.
- T1.10 can move rule 1 and the lower/upper splits onto the shared tokenizer only where ADR 0001's
  word rule gives the same words; rules 2 and the digit rule are specific to identifiers.

## Cases

`tests/test_cases.py` asserts every row (`ToSnakeCaseTest.test_adr_table`).

| Input | Output | Why |
|-------|--------|-----|
| `HTTPServer` | `http_server` | rule 2: the acronym ends before `Server` |
| `parseURL2` | `parse_url2` | rule 3, and the digit stays with `URL` |
| `camelCase` | `camel_case` | rule 3 |
| `PascalCase` | `pascal_case` | rule 3; the leading capital starts no empty word |
| `kebab-case` | `kebab_case` | rule 1 |
| `already_snake` | `already_snake` | rule 1; unchanged |
| `""` | `""` | no words |
| `getHTTPResponseCode` | `get_http_response_code` | rules 2 and 3 together |
| `HTTP2Server` | `http2_server` | rule 3 after a digit |
| `Version2Beta` | `version2_beta` | rule 3 after a digit |
| `userID` | `user_id` | rule 3; a trailing acronym stays whole |
| `ABC` | `abc` | a run of capitals alone is one word |
| `SCREAMING_SNAKE` | `screaming_snake` | rule 1, then lower-cased |
| `kebab-Case` | `kebab_case` | rule 1; mixed case across a separator |
| `a--b` | `a_b` | rule 1: a run of separators is one |
| `_private` | `private` | rule 1: leading separators dropped |
| `-` | `""` | separators only |
| `iOS` | `i_os` | rule 3; see Consequences |
| `hello world` | `hello world` | a space is not a separator |
