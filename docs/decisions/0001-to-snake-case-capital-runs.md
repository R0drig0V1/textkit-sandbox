<!-- ADR 0001: how to_snake_case splits runs of capitals and digits. -->
# 0001. How `to_snake_case` splits runs of capitals

Status: accepted (T1.7)

## Context

`textkit.cases.to_snake_case(name)` turns camelCase, PascalCase and kebab-case identifiers
into snake_case. Splitting at every capital gives `h_t_t_p_server` for `HTTPServer`, and
splitting only after a lower-case character gives `httpserver`; neither is what a reader
expects. Digits raise the same question (`parseURL2`, `utf8Encode`). The rule is decided once
here because `to_kebab_case` (T2.3) is built on `to_snake_case`, and T1.10 compares it with
the word rule of `word_count`.

## Decision

1. **Separators.** `_` and `-` separate words; a run of them counts as one, and separators
   at either end are dropped. These are the separators `to_camel_case` (T1.8) uses too.
2. **Case boundaries.** Inside each separator-free chunk, a new word starts at an upper-case
   character that:
   - follows a lower-case character or a digit (`camelCase` -> `camel` `Case`,
     `utf8Encode` -> `utf8` `Encode`); or
   - is the last capital of a run of two or more and is followed by a lower-case character
     (`HTTPServer` -> `HTTP` `Server`). A run of capitals at the end of the chunk, or before
     a digit, stays one word (`parseURL` -> `parse` `URL`, `parseURL2` -> `parse` `URL2`).
3. **Digits never start a word.** They stay with whatever comes before them, letters or
   capitals (`parseURL2` -> `parse_url2`, `Vector3D` -> `vector3_d`).
4. The words are lower-cased (`str.lower`) and joined with `_`.
5. "Upper-case" and "lower-case" are `str.isupper` and `str.islower`, so non-ASCII letters
   follow the same rule (`ÉtéÀ` -> `été_à`). Any other character (spaces, `.`, `$`) is not a
   separator and is kept, lower-cased; such input is outside the supported cases.
6. A `name` that is not a `str` raises `TypeError`.

This is the rule of the common `([A-Z]+)([A-Z][a-z])` / `([a-z\d])([A-Z])` underscore
conversion (for example Rails' `underscore`), so its results match what most readers already
expect.

## Consequences

- Acronyms survive as one word (`http_server`, `io_error`), at the cost of acronym-to-word
  joins with no lower-case character after them being kept together (`ABCdef` -> `ab_cdef`).
- A trailing capital after a digit becomes its own word (`Vector3D` -> `vector3_d`), and
  `version2Beta` -> `version2_beta`; there is no way to keep `3D` together.
- Conversion loses information: `HTTPServer` and `HttpServer` both give `http_server`, and
  `__init__` gives `init`, so `to_snake_case` is not reversible.
- snake_case input is a fixed point (`already_snake` -> `already_snake`), which T2.3 relies on.

## Table of cases

`tests/test_cases.py` tests every row.

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
| `parseURL` | `parse_url` |
| `utf8Encode` | `utf8_encode` |
| `Vector3D` | `vector3_d` |
| `IOError` | `io_error` |
| `ABCdef` | `ab_cdef` |
| `HTTP` | `http` |
| `Kebab-Case-Name` | `kebab_case_name` |
| `mixed-styles_andCase` | `mixed_styles_and_case` |
| `__init__` | `init` |
| `a--b__c` | `a_b_c` |
| `-` | `""` |
| `ÉtéÀ` | `été_à` |
