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

1. **After separators.** Any run of characters that are neither letters, digits nor
   combining marks (`-`, `_`, spaces, dots, ...) ends the current word and is dropped. Runs
   collapse to one `_` and separators at either end disappear, leading underscores
   included. A **combining mark** (Unicode category `M*`) is never a separator: it
   continues the word it follows and never starts one, exactly as in ADR 0001. A mark with
   no word to attach to (at the start of the name, or right after a separator) has no base
   letter and is dropped.
2. **At a lower-to-upper change.** An upper-case letter that follows a lower-case letter or
   a digit starts a word.
3. **Before the last capital of an acronym.** In a run of two or more capitals followed by
   a lower-case letter, the last capital starts the next word, so the acronym stays whole.
   A run of capitals at the end of a chunk, or followed by a digit, stays one word.

Digits are caseless: they never start a word on their own and stay with the word they
follow. Text with no case change and no separators is never split, so snake_case (and
plain lower-case) input comes back unchanged. Letters that are not upper case, including
caseless scripts, count as lower case. Input that is not a `str` raises `TypeError`.

Rules 2 and 3 compare *base letters*: when they look at the character before or after a
capital, they skip combining marks. In decomposed (NFD) text `"É"` is `"E"` + U+0301, and
the accent must not hide the capital (`ÉTÉFini`) or the lower-case letter after it
(`XMLÉtude`). So composed (NFC) and decomposed input give the same words. The text is
not normalised: the result keeps the input's form (NFD in, NFD out), which is what lets
snake_case input come back unchanged in either form.

Examples (each row is checked by `tests/test_cases.py`, once as written, which is NFC,
and once with input and output decomposed to NFD):

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
| `résuméFile` | `résumé_file` | 2; accents stay in the word |
| `caféAuLait` | `café_au_lait` | 2 |
| `ÉTÉFini` | `été_fini` | 3; marks skipped before a capital |
| `XMLÉtude` | `xml_étude` | 3; marks skipped after a capital |
| `naïve-Über` | `naïve_über` | 1 |
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
- T1.10 moved rule 1's character test onto the shared tokenizer: `to_snake_case` reads
  `textkit._tokens.char_class` (not `textkit._tokens.words`), and every example above is
  unchanged. The mark rule already agrees with ADR 0001's. The joiner and
  number-separator rules do not apply here: in an identifier `-` and `.` always separate
  (`kebab-case` is two words), so `to_snake_case` shares the character classes but not
  ADR 0001's word regex.
- A stray combining mark at the start of a name or after a separator is lost.
