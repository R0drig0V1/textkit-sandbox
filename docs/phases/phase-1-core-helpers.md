<!-- Phase 1 of textkit: the core helpers. Each task is one pull request. -->
# Phase 1: core helpers

Each task is one pull request: code, tests, docstrings, its README table row and its
CHANGELOG line. Tasks with no "Depends on" can start at once.

- [x] **T1.1 `slugify`** in `textkit/strings.py`: `slugify(text) -> str` lower-cases, turns
      every run of non-alphanumeric characters into one `-` and strips `-` at both ends
      (`"Hello, World!"` -> `"hello-world"`). ASCII only: other characters are dropped.
- [x] **T1.2 `truncate`** in `textkit/strings.py`: `truncate(text, width, suffix="...") -> str`
      returns `text` unchanged when it fits in `width`, else cuts it so that the result,
      suffix included, is exactly `width` long. `width` smaller than the suffix raises
      `ValueError`.
- [x] **T1.3 `strip_accents`** in `textkit/strings.py`: `strip_accents(text) -> str` removes
      combining marks (`"Ñandú"` -> `"Nandu"`) with `unicodedata`.
- [x] **T1.4 `wrap`** in `textkit/strings.py`: `wrap(text, width) -> list[str]` splits text
      into lines of at most `width` characters at spaces; a word longer than `width` gets a
      line of its own. Write an ADR on what happens to existing newlines.
- [x] **T1.5 `word_count`** in a new module `textkit/counts.py`: `word_count(text) -> int`.
      Write an ADR on what counts as a word (hyphenated words, numbers, apostrophes).
- [x] **T1.6 `char_freq`** in `textkit/counts.py`: `char_freq(text) -> dict[str, int]`,
      counts of each non-space character, case-sensitive.
- [x] **T1.7 `to_snake_case`** in a new module `textkit/cases.py`:
      `to_snake_case(name) -> str` for camelCase, PascalCase and kebab-case input. Write an
      ADR on how runs of capitals are split (`HTTPServer`, `parseURL2`).
- [x] **T1.8 `to_camel_case`** in `textkit/cases.py`: `to_camel_case(name) -> str` for
      snake_case and kebab-case input (`"user_id"` -> `"userId"`).
- [x] **T1.9 `slug_title`** in `textkit/strings.py`: `slug_title(text, max_len) -> str`, a
      slug of at most `max_len` characters that never ends in `-`, built from `slugify`
      (and `truncate` if it fits). Depends on T1.1 and T1.2.
- [ ] **T1.10 shared tokenizer**: add `textkit/_tokens.py` with `words(text) -> list[str]`
      implementing the word rule of T1.5's ADR, and make `word_count` and `to_snake_case`
      use it where it applies, with no change in their results. Depends on T1.5 and T1.7.
