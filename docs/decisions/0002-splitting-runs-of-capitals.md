<!-- ADR 0002: how to_snake_case splits identifiers into words (runs of capitals, digits, separators). -->
# 0002. Splitting runs of capitals in `to_snake_case`

- Status: accepted
- Date: 2026-11-18
- Task: T1.7 (`to_snake_case` in `textkit/cases.py`)

## Context

`to_snake_case(name)` takes camelCase, PascalCase and kebab-case identifiers. The easy rule,
"an upper-case letter starts a new word", turns acronyms into letter soup: `HTTPServer`
would become `h_t_t_p_server` and `parseURL2` would become `parse_u_r_l2`. The opposite
rule, "a run of capitals is one word", gives `httpserver`. Digits raise the same question:
does `2` in `parseURL2` start a word, end one, or belong to one?

T1.8 (`to_camel_case`), T1.10 (the shared tokenizer) and T2.3 (`to_kebab_case`, built on
this function) depend on the rule chosen here, so it is pinned with a table of cases.

## Decision

The identifier is split into words, the words are lower-cased (`str.lower`) and joined with
`_`. Splitting follows these rules, in order:

1. **Separators.** `_` and `-` end a word. A run of them counts as one separator; leading
   and trailing separators are dropped, so `__init__` gives `init`. This matches T1.8's
   separators, so the two functions round-trip on plain identifiers.
2. **Lower or digit, then upper.** An upper-case character that follows a lower-case
   character or a digit starts a new word: `camelCase` -> `camel` + `Case`,
   `utf8Decode` -> `utf8` + `Decode`.
3. **End of a run of capitals.** Inside a run of capitals, the last capital starts a new
   word when a lower-case character follows it, because it is the first letter of a
   capitalised word: `HTTPServer` -> `HTTP` + `Server`, `IOError` -> `IO` + `Error`. A run
   at the end of the name, or followed by a digit or a separator, stays whole: `ABC` ->
   `abc`, `parseURL2` -> `parse` + `URL2`.
4. **Digits never start a word.** A digit belongs to the word before it (`v2beta` stays one
   word, `URL2Path` -> `URL2` + `Path`). Only rule 2 can end a word after a digit.

Everything else (spaces, `.`, other punctuation) is neither a separator nor a boundary: it
stays inside its word. Case is tested with `str.isupper`, `str.islower` and `str.isdigit`,
so non-ASCII letters follow the same rules; no Unicode normalization is applied.
A `name` that is not a `str` raises `TypeError`.

Alternatives rejected:

- *Every capital starts a word*: breaks every acronym (`h_t_t_p_server`).
- *A run of capitals is always one word*: glues the acronym to the next word
  (`httpserver`).
- *Digits as their own word* (`parse_url_2`): it splits version-like names such as `utf8`
  and `v2beta`, and `to_camel_case` could not undo it.

## Consequences

- Acronyms survive as one word and the following word is kept apart, which is what most
  style guides (PEP 8 included) expect when converting names like `HTTPServer`.
- The conversion is lossy: `HTTPServer` and `HttpServer` both give `http_server`, so
  `to_camel_case(to_snake_case(x))` does not always return `x`.
- A two-letter acronym before a capitalised word splits as expected (`IOError` ->
  `io_error`), but a capitalised word that is itself one letter cannot be told apart from
  the end of an acronym (`ABCd` -> `ab_cd`).
- T1.10 can reuse a shared tokenizer only where its rule splits the same way as this one;
  rules 2-4 are specific to identifiers.

## Cases

Inputs and outputs are Python string literals. `tests/test_cases.py` tests every row and
checks that this table and the test agree.

| Input | Output | Rule |
|-------|--------|------|
| `"HTTPServer"` | `"http_server"` | 3 |
| `"parseURL2"` | `"parse_url2"` | 2, 3, 4 |
| `"camelCase"` | `"camel_case"` | 2 |
| `"PascalCase"` | `"pascal_case"` | 2 |
| `"kebab-case"` | `"kebab_case"` | 1 |
| `"already_snake"` | `"already_snake"` | 1 |
| `""` | `""` | 1 |
| `"getHTTPResponseCode"` | `"get_http_response_code"` | 2, 3 |
| `"IOError"` | `"io_error"` | 3 |
| `"ABC"` | `"abc"` | 3 |
| `"ABCd"` | `"ab_cd"` | 3 |
| `"URL2Path"` | `"url2_path"` | 2, 4 |
| `"utf8Decode"` | `"utf8_decode"` | 2, 4 |
| `"v2beta"` | `"v2beta"` | 4 |
| `"SCREAMING_SNAKE"` | `"screaming_snake"` | 1, 3 |
| `"mixed-kebab_snakeCase"` | `"mixed_kebab_snake_case"` | 1, 2 |
| `"__init__"` | `"init"` | 1 |
| `"a--b__c"` | `"a_b_c"` | 1 |
| `"---"` | `""` | 1 |
| `"aB"` | `"a_b"` | 2 |
| `"A"` | `"a"` | 3 |
| `"ÉtéCase"` | `"été_case"` | 2 |
