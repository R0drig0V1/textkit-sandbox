<!-- Phase 3 of textkit: three text tools, each a package of several modules, the changes
     they need in the existing code, and four small helpers. Each task is one pull request. -->
# Phase 3: text tools

Phase 1's "Rules for every task" apply, with the additions below. Tasks with no "Depends on"
can start at once. Sizes: a small task is one function, as in phases 1 and 2; a medium task
changes code that other modules use; a large task is a package of at least three modules
and at least 40 tests.

## Rules added for phase 3

- **Packages.** A tool is a package `textkit/<tool>/` of several modules. Its public
  functions are the names in `__all__` of `textkit/<tool>/__init__.py` (a literal list of
  strings), defined in the package's modules and imported there; every other name in the
  package is private, whatever it is called. `scripts/check.sh` and `tests/test_api.py`
  already read `__all__`, so each public function needs, as before, a docstring, type hints,
  its README row (module cell `textkit.<tool>`), its CHANGELOG line and an example in
  `docs/usage.md`.
- **Tests** of `textkit/<tool>/` go in `tests/test_<tool>.py`; a large tool may split them
  into `tests/test_<tool>_<part>.py`.
- **The command line** discovers the functions of single-file modules only (T2.6); a tool's
  subcommand is written by the tool's task.
- **The slow check.** `scripts/check.sh` waits `TEXTKIT_CHECK_SECONDS` (75 by default)
  before it runs: the wait stands for the build and test suite of a real project. Never
  shorten or skip it. While working, run the unit tests directly
  (`python3 -m unittest tests.test_<x>`); run `scripts/check.sh` when the task is ready.
- **Errors.** Until T3.2 is merged, a function rejects a bad value with `ValueError`, as in
  phases 1 and 2. A task that is still open when T3.2 merges follows T3.2 on its next rebase.

## Tasks

- [ ] **T3.1 command registry** (medium): turn `textkit/__main__.py` into a package
      `textkit/cli/`, so that a tool adds a subcommand without editing a shared file.
      `textkit/cli/registry.py`: a `Command` (name, one-line summary, `configure(parser)`,
      `run(args) -> int`), `register(command)` and `commands()` (sorted by name; a duplicate
      name raises `RuntimeError`). `textkit/cli/functions.py`: the commands discovered from
      public functions, exactly as T2.6 defines them. `textkit/cli/main.py`: `_main`, the
      parser and `--version`. `textkit/__main__.py` keeps only the call (`sys.exit(_main())`
      under `if __name__ == "__main__":`). A tool adds its subcommand as one module
      `textkit/cli/<name>.py` that registers a `Command`; the modules of `textkit/cli/` are
      found with `pkgutil`, never listed by hand. `--help` lists the discovered functions
      under `commands:` as today and the registered ones under `tools:`.
      `textkit/cli/__init__.py` has `__all__ = []`: the package has no public functions.
      Behaviour does not change: `tests/test_cli.py` passes with only its imports changed.
      Add tests for the registry: a registered fake command is listed under `tools:`, runs,
      and its exit code comes back; a duplicate name raises. Update the README "Commands"
      section. CHANGELOG line: "Split the command line into `textkit/cli/`."
- [ ] **T3.2 error hierarchy** (medium): `textkit/errors.py` with `TextkitError(Exception)`
      and `InvalidValueError(TextkitError)`. Every `raise ValueError` in `textkit/` becomes
      `raise InvalidValueError` with the same message; `TypeError` for an argument of the
      wrong type stays. Write an ADR on why `InvalidValueError` does not inherit from
      `ValueError` (callers catch `TextkitError`; a `ValueError` that escapes textkit is then
      a bug, not a rejected input). The command line catches `TextkitError` where it caught
      `ValueError` (exit 1). Every test that expects `ValueError` from textkit follows, and
      so does every "Raises:" in a docstring. Add `tests/test_errors.py`: the hierarchy, and
      a test that parses every file of `textkit/` with `ast` and fails on any
      `raise ValueError`. `errors.py` defines classes only, so it has no README row; add a
      section "Errors" to `docs/usage.md`. CHANGELOG line: "Added `textkit.errors`:
      functions raise `InvalidValueError` instead of `ValueError`."
- [ ] **T3.3 tokens with offsets** (medium): in `textkit/_tokens.py`, `words(text)` returns
      `list[Token]` instead of `list[str]`, where `Token` is a `typing.NamedTuple` with
      `text: str`, `start: int` and `end: int`, and `text_argument[start:end] == token.text`.
      Every caller in `textkit/` and `tests/` follows (`word_count` stays
      `len(words(text))`). Amend ADR 0002 with a section on offsets: they count code points,
      and combining marks stay inside their word. `tests/test_tokens.py` checks the offset
      invariant on every row of ADR 0002's case table, on NFD input and on text with
      characters outside the BMP. No README row (a private module). CHANGELOG line:
      "`_tokens.words` returns tokens with their offsets."
- [ ] **T3.4 template engine** (large): package `textkit/template/` with at least
      `lexer.py`, `parser.py` and `renderer.py`. Public function:
      `render(template: str, context: dict[str, Any]) -> str`.
      Syntax: `{{ expr }}` prints a value, where `expr` is a dotted name (`user.name`
      follows dict keys only) with optional filters (`{{ title | slug | truncate:20 }}`);
      `{% if expr %} ... {% else %} ... {% endif %}`, truth as Python's `bool`;
      `{% for item in expr %} ... {% endfor %}` over a list, with `loop.index` (from 1)
      inside; `{# comment #}`; blocks nest; text outside tags is copied as is. Filters, a
      fixed table over the existing functions: `slug` (`slugify`), `snake`, `camel`,
      `kebab`, `squeeze`, `strip_accents`, `truncate:<width>`, and `upper` and `lower`.
      Errors: `TemplateSyntaxError(ValueError)` with `line` and `column` (both from 1) for an
      unclosed tag, an unknown tag or filter, a bad filter argument, and `else`, `endif` or
      `endfor` without their opening tag. Write an ADR on names missing from the context:
      empty text or an error, and what `if` does with one.
      Subcommand `python3 -m textkit render <template-file> <json-file>`, as
      `textkit/cli/render.py`: prints the result; exit 1 with `line:column: message` on
      stderr for a template error; exit 2 for a file that cannot be read or is not a JSON
      object.
      Also `docs/template.md` (the syntax, every filter, every error), an example in
      `docs/usage.md`, the README row and the CHANGELOG line. At least 40 tests over the
      three modules, every error case with its line and column among them.
      Depends on T3.1.
- [ ] **T3.5 Markdown to HTML** (large): package `textkit/markdown/` with at least
      `blocks.py`, `inlines.py` and `html.py`. Public function: `to_html(text: str) -> str`.
      Blocks: ATX headings (`#` to `######`); paragraphs (consecutive lines joined by one
      space); unordered lists (`-` or `*`) and ordered lists (`1.`), one level, an item being
      its line plus the following lines indented by two spaces or more; fenced code blocks
      (three backticks, an optional language: `<pre><code class="language-x">`); block
      quotes (`>`, holding paragraphs only); a horizontal rule (`---` alone on a line).
      Inlines: `**strong**`, `*em*`, `` `code` ``, `[text](url)`, and a backslash before
      `\`, `*`, `` ` ``, `[` or `]` to print it as is. Raw HTML is never passed through:
      `&`, `<`, `>` and `"` are escaped everywhere, inside code too. Output: one block
      element per line, each line ending in `\n`, no other whitespace added; `""` gives `""`.
      Write an ADR on what the subset leaves out and why raw HTML is escaped; it ends with a
      table of cases (input -> output) and the tests cover every row.
      Subcommand `python3 -m textkit markdown <file>`, as `textkit/cli/markdown.py`: prints
      the HTML; exit 2 for a file that cannot be read.
      Also `docs/markdown.md` (every block and inline with an example), an example in
      `docs/usage.md`, the README row and the CHANGELOG line. At least 40 tests over the
      three modules.
      Depends on T3.1.
- [ ] **T3.6 line diff** (large): package `textkit/diff/` with at least `lcs.py`,
      `unified.py` and `patch.py`. Public functions:
      `unified_diff(a: str, b: str, context: int = 3) -> str`,
      `apply_patch(text: str, patch: str) -> str` and
      `diff_words(a: str, b: str) -> list[tuple[str, str]]`.
      `unified_diff` compares lines (`str.splitlines(keepends=True)`) with its own longest
      common subsequence (no `difflib` in `textkit/`) and returns the unified format:
      `--- a` and `+++ b`, then hunks `@@ -l,s +l,s @@` with `context` lines around each
      change; `""` when `a == b`; `context < 0` raises `ValueError`. Write an ADR on a text
      that does not end in a newline (the `\ No newline at end of file` marker).
      `apply_patch(a, unified_diff(a, b)) == b`: test it on a table of cases (an empty
      text, one line, no final newline on either side, a change in the first and in the
      last line, two hunks, two changes close enough to share a hunk) and on 200 random
      pairs from a seeded `random.Random`. `apply_patch` raises `PatchError(ValueError)`,
      naming the hunk, when a context or removed line does not match the text.
      `diff_words` returns `(op, word)` pairs, `op` being `"="`, `"-"` or `"+"`, over the
      words of `_tokens.words`, each word exactly as in its text.
      Subcommand `python3 -m textkit diff <file-a> <file-b>`, as `textkit/cli/diff.py`:
      prints the unified diff; exit 0 when the files are equal, 1 when they differ, 2 for a
      file that cannot be read.
      Also `docs/diff.md` (the format, the three functions, the errors), examples in
      `docs/usage.md`, the README rows and the CHANGELOG lines. At least 40 tests over the
      three modules.
      Depends on T3.1.
- [ ] **T3.7 `dedent`** (small) in `textkit/strings.py`: `dedent(text) -> str` removes the
      whitespace prefix common to every non-blank line (no `textwrap`). A line of
      whitespace only does not count for the prefix and becomes empty (its line ending
      stays); a tab and a space are different characters; `""` gives `""`.
- [ ] **T3.8 `center`** (small) in `textkit/strings.py`:
      `center(text, width, fill=" ") -> str` pads `text` on both sides to `width` code
      points; when the padding is odd, the extra `fill` goes on the right. A text of
      `width` or more is returned unchanged. `len(fill) != 1` or `width < 0` raises
      `ValueError`.
- [ ] **T3.9 `ngrams`** (small) in `textkit/counts.py`:
      `ngrams(text, n=2) -> list[tuple[str, ...]]`, the runs of `n` consecutive words
      (`_tokens.words`, each word exactly as in the text), in order. Fewer than `n` words
      give `[]`; `n < 1` raises `ValueError`.
- [ ] **T3.10 `levenshtein`** (small) in `textkit/strings.py`: `levenshtein(a, b) -> int`,
      the edit distance over code points (insert, delete, substitute, each of cost 1), with
      two rows of memory. `levenshtein("", s) == len(s)`; it is symmetric: test both.
