<!-- How textkit is put together: modules, the shared tokenizer, what counts as public. -->
# Architecture

`textkit` is one package of small, independent modules, one per topic (`strings`, `counts`,
`cases`), plus private modules shared between them. Standard library only.

## Public and private modules

A **public function** is a top-level `def` whose name does not start with `_`, in a module
of `textkit/` whose name does not start with `_` (phase 1, "Rules for every task"). Public
functions get a README row and a CHANGELOG line; `scripts/check.sh` enforces both and skips
every module whose name starts with `_` (`__init__.py`, `_tokens.py`, `__main__.py`).

## Shared tokenizer (`textkit/_tokens.py`)

`words(text) -> list[str]` returns the words of a text by the rule of
[ADR 0002](decisions/0002-what-counts-as-a-word.md): letters and digits, combining marks
inside a word, one `-`/`'`/`’` between word characters, one `.`/`,` between decimal digits.
`tests/test_tokens.py` checks every row of that ADR's table, word by word.

Who uses it:

- `counts.word_count` is exactly `len(words(text))`.
- `cases.to_snake_case` uses it for the separator step of
  [ADR 0001](decisions/0001-to-snake-case-word-boundaries.md) only when the name contains
  nothing but letters, digits and `_`; there the two rules cut at the same places. Names
  with `-` or any other character keep the `[-_]+` split, because ADR 0002 joins a single
  `-` and drops punctuation that ADR 0001 keeps inside a word. Case boundaries (ADR 0001
  rules 2-4) have no counterpart in ADR 0002 and stay in `cases._split_chunk`.
- `counts.sentence_count` does not use it: it needs only ADR 0002's word character
  (`str.isalnum()`), not whole words; its sentence rule is
  [ADR 0005](decisions/0005-what-ends-a-sentence.md).

Changing the word rule changes every caller, so it needs a new ADR that supersedes 0002.

## Helpers built on other helpers

Some public functions are defined in terms of others, so a change to the inner one changes
the outer one too:

- `strings.slug_title` is `truncate(slugify(text), max_len, suffix="")` with trailing `-`
  stripped.
- `strings.is_palindrome` normalizes with `strip_accents`, then `str.casefold()`, and keeps
  only `str.isalnum()` characters before comparing the text with its reverse.
