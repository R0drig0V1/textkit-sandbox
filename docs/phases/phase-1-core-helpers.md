<!-- Phase 1 of textkit: the core helpers. Each task is one pull request. -->
# Phase 1: core helpers

Each task is one pull request: code, tests, docstrings and, for each public function it adds
or changes, its README table row and CHANGELOG line (`scripts/check.sh` rejects rows for
anything else). Tasks with no "Depends on" can start at once.

## Rules for every task (phases 1 and 2)

- **Public function** (one definition for `scripts/check.sh`, the README table, the
  CHANGELOG, T2.5, T2.6 and T2.8): a top-level `def` whose name does not start with `_`, in a
  module of `textkit/` whose name does not start with `_`. So `_tokens.py` and `__main__.py`
  contain no public functions; helpers in public modules start with `_`.
- **Depends on X** means X is merged into the base branch, its ADR included. A dependent task
  reads that ADR from the base branch and cites its number in its PR body.
- **Tests** for `textkit/<m>.py` go in `tests/test_<m>.py`, one `unittest.TestCase` class per
  function, named `<FunctionInCamelCase>Test`. Exceptions: `textkit/_tokens.py` ->
  `tests/test_tokens.py`; `textkit/__main__.py` -> `tests/test_cli.py` (T2.6 creates it, T2.7
  extends it).
- **Placement**, to keep merges trivial: README rows and CHANGELOG lines are inserted in
  alphabetical order of function name; functions in a module and test classes in a test file
  are appended at the end. A purely additive conflict after another PR merged is resolved by
  the author on rebase, keeping both sides and changing nothing else.
- **Python 3.9**: `Optional[X]` / `Union[...]` from `typing` (no `X | Y`), no
  `from __future__ import annotations`, no `match`. Built-in generics (`list[str]`,
  `dict[str, int]`) are fine. Green means `scripts/check.sh` passes under Python 3.9.

## Tasks

- [x] **T1.1 `slugify`** in `textkit/strings.py`: `slugify(text) -> str` lower-cases, turns
      every run of non-alphanumeric characters into one `-` and strips `-` at both ends
      (`"Hello, World!"` -> `"hello-world"`). ASCII only: characters outside ASCII are removed
      first, with no separator (`"naïve"` -> `"nave"`, `"Ñandú"` -> `"and"` for NFC input as
      typed; no Unicode normalization is applied, so NFD input gives `"nandu"`: test both);
      then every run of characters outside `[a-z0-9]` after lower-casing (`_` included) becomes one `-`.
      `""` and `"!!!"` give `""`. Do not use `str.isalnum` (it accepts non-ASCII).
- [x] **T1.2 `truncate`** in `textkit/strings.py`: `truncate(text, width, suffix="...") -> str`
      returns `text` unchanged when it fits in `width`, else cuts it so that the result,
      suffix included, is exactly `width` long. `width` smaller than the suffix raises
      `ValueError`, whenever `width < len(suffix)`, even if `text` fits. "Fits" means
      `len(text) <= width` (code points); the cut keeps the start of `text`.
- [x] **T1.3 `strip_accents`** in `textkit/strings.py`: `strip_accents(text) -> str` removes
      combining marks (`"Ñandú"` -> `"Nandu"`) with `unicodedata`.
- [ ] **T1.4 `wrap`** in `textkit/strings.py`: `wrap(text, width) -> list[str]` splits text
      into lines of at most `width` characters at spaces; a word longer than `width` gets a
      line of its own. Runs of spaces between words collapse to one; leading and trailing
      spaces are dropped; `wrap("", w) == []`; `width < 1` raises `ValueError`; lines never
      contain the separating space. Write an ADR on what happens to existing newlines.
- [ ] **T1.5 `word_count`** in a new module `textkit/counts.py`: `word_count(text) -> int`.
      Write an ADR on what counts as a word (hyphenated words, numbers, apostrophes). The ADR
      ends with a table of cases (input -> count), at least: a hyphenated word, a number, a
      word with an apostrophe, `""`, punctuation only, several spaces/newlines;
      `tests/test_counts.py` tests every row.
- [ ] **T1.6 `char_freq`** in `textkit/counts.py`: `char_freq(text) -> dict[str, int]`,
      counts of each non-space character, case-sensitive. Characters for which
      `str.isspace()` is true are not counted; keys appear in order of first occurrence.
      Depends on T1.5 (it creates `textkit/counts.py` and `tests/test_counts.py`).
- [x] **T1.7 `to_snake_case`** in a new module `textkit/cases.py`:
      `to_snake_case(name) -> str` for camelCase, PascalCase and kebab-case input. Write an
      ADR on how runs of capitals are split (`HTTPServer`, `parseURL2`). The ADR ends with a
      table of cases (input -> output), at least: `HTTPServer`, `parseURL2`, `camelCase`,
      `PascalCase`, `kebab-case`, `already_snake`, `""`; `tests/test_cases.py` tests every row.
- [ ] **T1.8 `to_camel_case`** in `textkit/cases.py`: `to_camel_case(name) -> str` for
      snake_case and kebab-case input (`"user_id"` -> `"userId"`). Separators are `_` and `-`
      (a run of them counts as one); leading and trailing separators are dropped; the first
      word is lower-cased and the rest capitalized (`"HTTP_server"` -> `"httpServer"`); input
      with no separator is returned with only its first character lower-cased.
      Depends on T1.7 (it creates `textkit/cases.py` and `tests/test_cases.py`).
- [ ] **T1.9 `slug_title`** in `textkit/strings.py`: `slug_title(text, max_len) -> str`, a
      slug of at most `max_len` characters that never ends in `-`: exactly
      `truncate(slugify(text), max_len, suffix="")` with trailing `-` stripped (a character
      cut, not a word cut). `max_len < 0` raises `ValueError`; the result may be `""`.
      Examples to test: `("Hello, World!", 8)` -> `"hello-wo"`, `("Hello, World!", 6)` ->
      `"hello"`, `("Hello, World!", 11)` -> `"hello-world"`, `("x", 0)` -> `""`.
      Depends on T1.1 and T1.2.
- [ ] **T1.10 shared tokenizer**: add `textkit/_tokens.py` (a private module: no README row,
      no CHANGELOG line) with `words(text) -> list[str]` implementing exactly the word rule of
      T1.5's ADR, and make `word_count` return `len(words(text))`. Make `to_snake_case` use
      `words` only for the parts where T1.5's rule and T1.7's ADR split the same way;
      otherwise leave it unchanged and say why in the PR body. Update `scripts/check.sh` in
      the same PR so that modules whose name starts with `_` are skipped. Acceptance:
      `tests/test_tokens.py` has one assertion per row of T1.5's ADR table, and the PR body
      lists which rows of T1.7's table now go through `words`; the PR does not modify
      the existing tests in `tests/test_counts.py` or `tests/test_cases.py`, and they pass.
      Depends on T1.5 and T1.7.
