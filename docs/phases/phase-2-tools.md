<!-- Phase 2 of textkit: tools built on the core helpers. Each task is one pull request. -->
# Phase 2: tools

Same rules as phase 1. Tasks with no "Depends on" can start at once.

- [x] **T2.1 `reading_time`** in `textkit/counts.py`: `reading_time(text, wpm=200) -> int`,
      whole minutes, from `word_count`. Write an ADR on rounding (an empty text, under one
      minute). Depends on T1.5.
- [x] **T2.2 `sentence_count`** in `textkit/counts.py`: `sentence_count(text) -> int`.
      Write an ADR on abbreviations (`"e.g."`, `"Dr."`) and ellipses.
- [x] **T2.3 `to_kebab_case`** in `textkit/cases.py`: `to_kebab_case(name) -> str`, built on
      `to_snake_case`. Depends on T1.7.
- [x] **T2.4 `is_palindrome`** in `textkit/strings.py`: `is_palindrome(text) -> bool`,
      ignoring case, spaces, punctuation and accents (use `strip_accents`). Depends on T1.3.
- [ ] **T2.5 API contract test**: `tests/test_api.py` checks that every public function of
      every `textkit` module has a docstring and type hints for all parameters and the
      return value, and fix any function that does not. Depends on T1.1 to T1.8.
- [ ] **T2.6 command line**: `textkit/__main__.py` so that `python3 -m textkit <function>
      <text>` prints the result of any public function of one text argument, and lists them
      with `--help`. Depends on T1.1 to T1.8.
- [ ] **T2.7 `--version`**: `textkit.__version__ = "0.1.0"` and `python3 -m textkit
      --version`. Depends on T2.6.
- [ ] **T2.8 usage guide**: `docs/usage.md` with one short example per public function, and
      a test that runs every example. Depends on every other task of phases 1 and 2.
