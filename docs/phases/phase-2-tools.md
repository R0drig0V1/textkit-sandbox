<!-- Phase 2 of textkit: tools built on the core helpers. Each task is one pull request. -->
# Phase 2: tools

Same rules as phase 1 (its "Rules for every task" section). Tasks with no "Depends on" can
start at once.

- [ ] **T2.1 `reading_time`** in `textkit/counts.py`: `reading_time(text, wpm=200) -> int`,
      whole minutes, from `word_count`. Write an ADR on rounding (an empty text, under one
      minute). `wpm < 1` raises `ValueError`. Depends on T1.5.
- [ ] **T2.2 `sentence_count`** in `textkit/counts.py`: `sentence_count(text) -> int`.
      Write an ADR on abbreviations (`"e.g."`, `"Dr."`) and ellipses. Depends on T1.5 (it
      creates `textkit/counts.py`).
- [ ] **T2.3 `to_kebab_case`** in `textkit/cases.py`: `to_kebab_case(name) -> str`, built on
      `to_snake_case`. Depends on T1.7.
- [ ] **T2.4 `is_palindrome`** in `textkit/strings.py`: `is_palindrome(text) -> bool`,
      ignoring case, spaces, punctuation and accents (use `strip_accents`). Only characters
      with `str.isalnum()` are kept after `strip_accents` and `casefold()`; digits count; `""`
      and text with no alphanumerics return `True`. Depends on T1.3.
- [x] **T2.5 API contract test**: `tests/test_api.py` checks that every public function of
      every `textkit` module has a docstring and type hints for all parameters and the
      return value, and fix any function that does not. No hard-coded lists: the test
      discovers modules with `pkgutil.iter_modules(textkit.__path__)` and functions with
      `inspect.getmembers(m, inspect.isfunction)` filtered on `f.__module__ == m.__name__`,
      applying the public-function definition of phase 1; it reads hints with
      `typing.get_type_hints` (so an annotation that does not evaluate on the running Python
      fails), and asserts the discovered set equals the README function table.
      Depends on T1.1 to T1.8.
- [ ] **T2.6 command line**: `textkit/__main__.py` so that `python3 -m textkit <function>
      <text>` prints the result of any public function of one text argument, and lists them
      with `--help`. Entry point `_main(argv: Optional[List[str]] = None) -> int`, called
      under `if __name__ == "__main__":` (importing the module has no side effects).
      Commands are discovered at run time, never hard-coded: every public function (phase 1
      definition) whose `f.__module__` is its own module and that has exactly one parameter
      without a default (parameters with defaults keep their default). Exactly one text
      argument (quote it). Output: `str` printed as is; `bool` and `int` with `print()`;
      `dict` and `list` as `json.dumps(result, ensure_ascii=False, sort_keys=True)`. Exit 0
      on success, 2 on an unknown function or a wrong argument count, with the message on
      stderr. With no arguments it prints the usage to stderr and exits 2 (argparse on 3.9:
      `add_subparsers(dest="command", required=True)`; `dest` is mandatory there); test
      it. `--help` lists every command with the first line of its docstring. Acceptance: a
      test asserts the `--help` command list equals the set computed from the
      public-function definition, and runs every command once via `subprocess` with
      `sys.executable -m textkit`. Add the CHANGELOG line "Added the `python3 -m textkit`
      command line." (no README row). Depends on T1.1 to T1.8.
- [ ] **T2.7 `--version`**: `__version__ = "0.1.0"` in `textkit/__init__.py` (the only place
      in `textkit/` the version string appears; `__main__.py` reads `textkit.__version__`);
      `python3 -m textkit --version` prints exactly `textkit 0.1.0` and exits 0. Test via
      `subprocess` with `sys.executable`: the output equals `f"textkit {textkit.__version__}\n"`
      and, separately, `textkit.__version__ == "0.1.0"`. CHANGELOG line: "Added
      `python3 -m textkit --version`." Depends on T2.6.
- [ ] **T2.8 usage guide**: `docs/usage.md` with one short example per public function, and
      a test that runs every example. The examples are doctest blocks
      (`>>> from textkit.<module> import <f>`); `tests/test_usage.py` loads
      `pathlib.Path(__file__).resolve().parents[1] / "docs" / "usage.md"` as
      `doctest.DocFileSuite(str(path), module_relative=False)` through a `load_tests` hook (or
      asserts `doctest.testfile(...).failed == 0` and `attempted > 0`), and asserts that every
      public function is called in at least one `>>>` line (`\b<f>\(`). A deliberately wrong
      example must make `scripts/check.sh` red (state in the PR body that this was tried).
      Depends on every other task of phases 1 and 2.
