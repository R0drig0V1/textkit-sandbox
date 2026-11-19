<!-- ADR 0002: where to_snake_case splits words (runs of capitals, digits, separators). -->
# 0002. Word boundaries in `to_snake_case`

## Context

`textkit.cases.to_snake_case(name)` (plan task T1.7) turns camelCase, PascalCase and
kebab-case identifiers into snake_case. Splitting at every capital is not enough: acronyms
(`HTTPServer`, `parseURL`) and digits (`parseURL2`, `utf8Decode`) have several plausible
answers, and the choice is hard to change once callers rely on it. `to_kebab_case` (T2.3)
will be built on `to_snake_case`, so it inherits these rules too.

## Decision

A name is split into words, the words are lower-cased and joined with `_`. A new word
starts:

1. **After separators.** Any run of characters that are neither letters nor digits (`-`,
   `_`, spaces, dots, ...) ends the current word and is dropped. Runs collapse to one `_`
   and separators at either end disappear, leading underscores included.
2. **At a lower-to-upper change.** An upper-case letter that follows a lower-case letter or
   a digit starts a word.
3. **Before the last capital of an acronym.** In a run of two or more capitals followed by
   a lower-case letter, the last capital starts the next word, so the acronym stays whole.
   A run of capitals at the end of a chunk, or followed by a digit, stays one word.

Digits are caseless: they never start a word on their own and stay with the word they
follow. Text with no case change and no separators is never split, so snake_case (and
plain lower-case) input comes back unchanged. Letters that are not upper case, including
caseless scripts, count as lower case. Input that is not a `str` raises `TypeError`.

Examples (each row is checked by `tests/test_cases.py`):

| Input | Output | Rule |
|-------|--------|------|
| `parseUrl` | `parse_url` | 2 |
| `PascalCase` | `pascal_case` | 2 |
| `HTTPServer` | `http_server` | 3 |
| `getHTTPResponseCode` | `get_http_response_code` | 2, 3 |
| `IOError` | `io_error` | 3 |
| `parseURL` | `parse_url` | 2; acronym at the end stays whole |
| `parseURL2` | `parse_url2` | digit stays with `URL` |
| `URL2Path` | `url2_path` | 2 (digit then capital) |
| `HTTP2Server` | `http2_server` | 2 (digit then capital) |
| `utf8Decode` | `utf8_decode` | 2 (digit then capital) |
| `base64` | `base64` | digits never split |
| `version2beta` | `version2beta` | no case change, no split |
| `ABC` | `abc` | one run of capitals |
| `aB` | `a_b` | 2 |
| `kebab-case` | `kebab_case` | 1 |
| `my-HTTPServer` | `my_http_server` | 1, 3 |
| `user_id` | `user_id` | already snake: unchanged |
| `SCREAMING_SNAKE` | `screaming_snake` | 1 |
| `user--id` | `user_id` | 1, runs collapse |
| `_private` | `private` | 1, ends dropped |
| `user name.v2` | `user_name_v2` | 1, any non-alphanumeric |
| (empty) | (empty) | nothing to split |

## Consequences

- Acronyms read naturally (`http_server`, not `h_t_t_p_server`), at the cost of not
  round-tripping: `to_camel_case("http_server")` (T1.8) gives `httpServer`, not
  `HTTPServer`.
- An acronym directly followed by a digit and a lower-case word stays glued
  (`ABC2def` -> `abc2def`), because the digit hides the case change. Rare in practice.
- Leading and trailing underscores are lost (`__init__` -> `init`); callers that need
  dunder or private names must keep them themselves.
- `to_kebab_case` (T2.3) can be `to_snake_case(name).replace("_", "-")`.
- T1.10 may move rule 1 onto the shared tokenizer `textkit._tokens.words`; it must keep
  every example above unchanged.
