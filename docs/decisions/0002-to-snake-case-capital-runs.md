<!-- ADR 0001: how to_snake_case splits words, in particular runs of capitals and digits. -->
# 0002. How `to_snake_case` splits runs of capitals

## Context

`textkit.cases.to_snake_case` (plan task T1.7) turns camelCase, PascalCase and kebab-case
identifiers into snake_case. Splitting at each lower-to-upper change is not enough: names
with acronyms (`HTTPServer`, `parseURL2`, `userID`) and digits (`utf8Encode`, `HTTP2Server`)
can be split several ways, and each way is defensible:

- one word per capital: `HTTPServer` -> `h_t_t_p_server`; unreadable and not reversible;
- the whole run of capitals as one word: `HTTPServer` -> `httpserver`; loses the boundary;
- the run minus its last capital, which starts the next word: `HTTPServer` -> `http_server`.

Digits raise the same question: `parseURL2` could give `parse_url2` or `parse_url_2`.
T1.8 (`to_camel_case`) and T1.10 (the shared tokenizer) build on this rule, so it is fixed
here, together with a table of cases that `tests/test_cases.py` checks row by row.

## Decision

Words are split as follows, and then lower-cased and joined with a single `_`:

1. **Separators.** A run of `-` and/or `_` is one boundary. Leading and trailing separators
   are dropped, so `"__private__"` gives `"private"` and separators only give `""`.
2. **Lower or digit, then upper.** A capital that follows a lower-case letter or a digit
   starts a new word: `camelCase` -> `camel_case`, `utf8Encode` -> `utf8_encode`.
3. **Runs of capitals.** In a run of two or more capitals followed by a lower-case letter,
   the last capital starts the next word and the rest of the run is one word:
   `HTTPServer` -> `http_server`, `IOError` -> `io_error`. A run of capitals that is not
   followed by a lower-case letter (it ends the name, or a digit or separator follows) stays
   one word: `userID` -> `user_id`, `parseURL2` -> `parse_url2`.
4. **Digits** never start a word: they stay with the word before them, whether that word is
   lower-case or a run of capitals (`version2`, `parse_url2`, `http2_server`). Only rule 2
   splits after a digit.
5. **Other characters.** Boundaries are detected on ASCII letters and digits only. Any other
   character (spaces, punctuation, non-ASCII letters) stays where it is, is lower-cased by
   `str.lower`, and never splits a word. Supported input is camelCase, PascalCase and
   kebab-case; anything else is converted on a best-effort basis by the same rules.

The implementation is two regular-expression substitutions per separator-delimited part
(`([A-Z]+)([A-Z][a-z])` for rule 3, then `([a-z0-9])([A-Z])` for rule 2), the same approach
as common inflection libraries, so the results match what most readers expect.

## Consequences

- Acronyms stay readable and boundaries survive: `getHTTPResponseCode` ->
  `get_http_response_code`.
- The conversion is not reversible: `HTTPServer` and `HttpServer` both give `http_server`,
  so `to_camel_case` (T1.8) cannot restore the original capitals.
- Two acronyms in a row cannot be told apart (`HTTPAPI` -> `httpapi`); callers who need the
  boundary must write `HttpApi` or `http-api`.
- Keeping digits with the previous word means `parse2URL` gives `parse2_url`, never
  `parse_2_url`. A later change to split digits off would alter outputs and needs a new ADR.
- The output is already snake_case, so a second call changes nothing (tested).
- T1.10 may reuse the shared tokenizer only where its word rule splits the same way as
  rules 1 to 5 above.

## Cases

`tests/test_cases.py` asserts every row (and that this table and the test list match).
Values are Python string literals.

| Input | Output |
|-------|--------|
| `"HTTPServer"` | `"http_server"` |
| `"parseURL2"` | `"parse_url2"` |
| `"camelCase"` | `"camel_case"` |
| `"PascalCase"` | `"pascal_case"` |
| `"kebab-case"` | `"kebab_case"` |
| `"already_snake"` | `"already_snake"` |
| `""` | `""` |
| `"getHTTPResponseCode"` | `"get_http_response_code"` |
| `"userID"` | `"user_id"` |
| `"IOError"` | `"io_error"` |
| `"HTTP"` | `"http"` |
| `"HTTP2Server"` | `"http2_server"` |
| `"utf8Encode"` | `"utf8_encode"` |
| `"parse2URL"` | `"parse2_url"` |
| `"Kebab-Case"` | `"kebab_case"` |
| `"mixed-camelCase"` | `"mixed_camel_case"` |
| `"HTTP_Server"` | `"http_server"` |
| `"a--b__c"` | `"a_b_c"` |
| `"__private__"` | `"private"` |
| `"--"` | `""` |
