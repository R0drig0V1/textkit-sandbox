<!-- Phase 3 of textkit: three text tools, each a package of several modules, the changes
     they need in the existing code, and four small helpers. Each task is one pull request.
     Reviewed in docs/plan-reviews/2026-11-20-phase-3.md. -->
# Phase 3: text tools

Phase 1's "Rules for every task" apply, with the additions below. Tasks with no "Depends on"
and no "PR after" can start at once. Sizes: a small task is one function, as in phases 1 and
2; a medium task changes code that other modules use; a large task is a package of at least
three modules and at least 40 tests.

**Order.** Start at once: T3.1, T3.3, T3.4, T3.5, T3.6, T3.7, T3.8, T3.10 (the "PR after"
tasks too: writing their code early is the point of the relation, and their briefs carry
the "PR after" line). T3.2 depends on T3.1; T3.9 depends on T3.3. T3.4 and T3.5 open their
PR after T3.1 is merged; T3.6 after T3.1 and T3.3. T3.8 opens its PR after T3.7, and T3.10
after T3.8: all three append to the end of `textkit/strings.py`, `tests/test_strings.py` and
the Strings section of `docs/usage.md`, so each rebases onto the previous one instead of
being bounced for a conflict. Once T3.2's PR is open, the integrator verifies it before any
other phase 3 PR except T3.1's, so a PR that raises errors does not land under it and
bounce it.

## Rules added for phase 3

- **Packages.** A tool is a package `textkit/<tool>/` of several modules. Its public
  functions are the names in `__all__` of `textkit/<tool>/__init__.py` (a literal list of
  strings), defined in the package's modules and imported there; every other name in the
  package is private, whatever it is called. `scripts/check.sh` and `tests/test_api.py`
  already read `__all__`, so each public function needs, as before, a docstring, type hints,
  its README row (module cell `textkit.<tool>`), its CHANGELOG line and an example in
  `docs/usage.md`. **Exception classes** a tool defines are importable from the package
  (`from textkit.template import TemplateSyntaxError`) but are never in `__all__`: it lists
  functions only, and `scripts/check.sh` asks a README row for every name in it.
- **Tests** of `textkit/<tool>/` go in `tests/test_<tool>.py`; a large tool may split them
  into `tests/test_<tool>_<part>.py`. "At least 40 tests" means 40 `test_*` methods
  (subtests do not count), and each of the task's named modules is imported and tested
  directly by at least 8 of them.
- **PR after X** (new in phase 3): the task starts at once, but its PR is opened only from a
  branch rebased onto a base branch that contains X; the PR body cites X's PR. "Depends on X"
  keeps its phase 1 meaning (the task starts after X is merged). Build what does not need X
  first (for T3.4-T3.6: the package, its tests and docs; `textkit/cli/<name>.py` last). When
  the task is otherwise ready and an X is not on `origin/<base>`, send the integrator
  `READY, WAITING FOR <every missing X>` (for example `READY, WAITING FOR T3.1, T3.3`) and
  stop. After every phase 3 merge, the integrator reads the "PR after" list in "Order" and
  tells each started task whose X are now all on `origin/<base>` to rebase and finish,
  whether or not it remembers a `READY` message (the plan, not a conversation, holds the
  waiting list). The integrator bounces a PR whose base lacks an X without running the
  checks.
- **The command line** discovers the functions of single-file modules only (T2.6); a tool's
  subcommand is written by the tool's task, as one module `textkit/cli/<name>.py` (T3.1).
  Every tool subcommand:
  - reads its files as UTF-8 with `newline=""` (no newline translation: the function sees
    the file's text exactly, `"\r"` included); a file that is missing, unreadable or not
    valid UTF-8 exits 2 with `python3 -m textkit <name>: error: <path>: <reason>` on stderr
    (the prefix built from `registry.PROG`, T3.1) and no traceback;
  - writes its result to stdout unchanged with `sys.stdout.write` (no newline added; nothing
    at all for an empty result);
  - handles its own errors in `Command.run` and returns the exit code;
  - is tested through `subprocess` with `sys.executable -m textkit`, every exit code at least
    once, with input files written to a `tempfile` directory (never fixed paths: checks run
    in parallel) and passed as absolute paths; the subprocess runs as `_run` in
    `tests/test_cli.py` does (cwd the repository root, `PYTHONIOENCODING=utf-8`), reusing
    that helper. `_run` decodes in text mode, which turns `"\r\n"` and `"\r"` into `"\n"`:
    a test whose expected stdout contains `"\r"` uses `_run_bytes` (T3.1) and compares with
    the expected text `.encode("utf-8")`; `_run` is for exit codes, stderr and output
    without `"\r"`;
  - adds one bullet to the README "Commands" section, in alphabetical order of subcommand.
- **The slow check.** `scripts/check.sh` waits `TEXTKIT_CHECK_SECONDS` (75 by default)
  before it runs: the wait stands for the build and test suite of a real project. Never
  shorten or skip it. While working, run the unit tests directly
  (`python3 -m unittest tests.test_<x>`); run `scripts/check.sh` when the task is ready.
- **Errors.** Until T3.2 is merged, a function rejects a bad value with `ValueError`, as in
  phases 1 and 2, and an exception class a task defines subclasses `ValueError`. Once T3.2
  is merged, functions raise `textkit.errors.InvalidValueError` and a task's exception
  classes subclass it. Whichever of T3.2 and another task merges second does the conversion
  on its rebase; T3.2's test (below) fails until it is done. A `ValueError` raised by the
  standard library inside textkit (`int("x")`, `json.loads`) never escapes: it is turned
  into the task's own error.
- **ADRs.** T3.2, T3.4, T3.5 and T3.6 each add one ADR; T3.3 amends ADR 0002 and adds none.
  A new ADR takes the next free number on your base branch (the highest on
  `origin/<base>` plus one), so the checks pass; when another lands first, the integrator
  renumbers yours at merge. Tests and code find an ADR by its slug (as
  `tests/test_tokens.py` does), never by its number. Its row in `docs/decisions/README.md`
  goes in number order. An ADR that ends with a table of cases follows ADR 0002: the table
  is the last section, `## Cases`; every cell is a Python literal in backticks that
  `ast.literal_eval` accepts (`str`, `int`, `bool`, `None`, tuple, dict; a `|` inside it
  written `\x7c`, a newline `\n`; ADR 0002's bare integer count cells stay as they are);
  the test finds the ADR by slug, parses the rows with `ast.literal_eval` and asserts that
  its own case list equals them, so the table and the tests cannot drift apart.
- **Placement** (adds to phase 1's): CHANGELOG lines that name no public function go at the
  end of `## Unreleased`. New sections of `docs/usage.md` (`## Diff: \`textkit.diff\``,
  `## Errors: \`textkit.errors\``, `## Markdown: \`textkit.markdown\``,
  `## Templates: \`textkit.template\``) go just before `## Command line`, in that
  alphabetical order; a small helper's example goes at the end of its module's section. An
  additive conflict in any of these files is resolved by the author on rebase.

## Tasks

- [x] **T3.1 command registry** (medium): turn `textkit/__main__.py` into a package
      `textkit/cli/`, so that a tool adds a subcommand without editing a shared file.
      `textkit/cli/registry.py`, exactly:
      `@dataclass(frozen=True) class Command` with `name: str`, `summary: str` (one line),
      `configure: Callable[[argparse.ArgumentParser], None]` and
      `run: Callable[[argparse.Namespace], int]`; `register(command: Command) -> Command`;
      `commands() -> list[Command]` (sorted by name); and the constant
      `PROG = "python3 -m textkit"`. `_main` adds each tool with
      `sub.add_parser(command.name, description=command.summary)`, calls `configure` on that
      parser and passes the whole namespace to `run`.
      Registering the same `Command` object again is a no-op; a different command with a name
      already registered raises `RuntimeError`. Tool names and function-command names share
      one namespace: a tool named like a function command raises `RuntimeError`, checked in
      `_main` after discovery and before parsing, so it fails on every run.
      `textkit/cli/functions.py`: the commands discovered from public functions, exactly as
      T2.6 defines them. `textkit/cli/main.py`: `_main`, the parser and `--version`.
      `textkit/__main__.py` keeps only the call (`sys.exit(_main())` under
      `if __name__ == "__main__":`). A tool adds its subcommand as one module
      `textkit/cli/<name>.py` that registers a `Command`; the modules of `textkit/cli/` are
      found with `pkgutil`, never listed by hand, and imported by an idempotent
      `_load_tools()` in `main.py` that `_main` calls, not when `main.py` is imported.
      `--help` prints `commands:` and the discovered functions as today, then a blank line,
      then `tools:` and the registered commands (no `tools:` block when none is registered).
      `_main` returns `Command.run`'s exit code as is; it catches `ValueError` around function
      commands only, as today. `textkit/cli/__init__.py` has `__all__ = []`: the package has
      no public functions.
      Behaviour does not change: `tests/test_cli.py` passes with only its imports changed
      (`import textkit.cli.main as cli`), so `textkit/cli/main.py` exposes `_main`,
      `_commands(modules) -> dict[str, Callable]` and `_textkit_modules()`, and `_main` looks
      `_textkit_modules` up in `main`'s globals so that
      `mock.patch.object(cli, "_textkit_modules", ...)` still works. The PR body states that
      the diff of `tests/test_cli.py` is its import lines, its module docstring (updated
      to name `textkit/cli/`) and one new helper, `_run_bytes(*args)`: `_run` without
      `text` and `encoding`, returning bytes (for the tools' `"\r"` tests); no change to a
      test body.
      Add `tests/test_cli_registry.py`: a registered fake command is listed under `tools:`,
      runs, and its exit code comes back; registering it twice is a no-op; a different command
      with the same name raises; a tool named like a function command raises. The tests
      restore the registry they change (`_load_tools()` then a snapshot in `setUp`, restore
      in `tearDown`), so no fake command leaks into other tests and no real tool is lost;
      a test checks that after a registry test `_main(["--help"])` still lists every tool
      module under `textkit/cli/`, also when the file is run alone. Update the README
      "Commands" section. CHANGELOG
      line: "Split the command line into `textkit/cli/`."
- [x] **T3.2 error hierarchy** (medium): `textkit/errors.py` with `TextkitError(Exception)`
      and `InvalidValueError(TextkitError)`. Every `raise ValueError` in `textkit/` becomes
      `raise InvalidValueError` with the same message; `TypeError` for an argument of the
      wrong type stays. Write an ADR on why `InvalidValueError` does not inherit from
      `ValueError` (callers catch `TextkitError`; a `ValueError` that escapes textkit is then
      a bug, not a rejected input). Exception classes already merged from T3.4 or T3.6
      subclass `InvalidValueError` (phase 3 rule "Errors"). The command line
      (`textkit/cli/main.py`) catches `TextkitError` where it caught `ValueError` (exit 1,
      message on stderr, no traceback); a plain `ValueError` is no longer caught. Every test
      that expects `ValueError` from textkit follows, and so do every "Raises:" in a
      docstring, the `truncate` doctest in `docs/usage.md` and the README "Commands" text.
      Add `tests/test_errors.py`:
      - the hierarchy (`InvalidValueError` is a `TextkitError`, not a `ValueError`);
      - a test that parses every `*.py` under `textkit/`, recursively (`rglob`), with `ast`,
        one subtest per file, and fails on any `raise ValueError`, any call `ValueError(...)`
        and any class with `ValueError` among its bases; it also asserts that at least one
        file in a subpackage (`textkit/cli/`) was parsed;
      - a test that imports every module that
        `pkgutil.walk_packages(textkit.__path__, "textkit.")` yields (subpackages included)
        and checks that every exception class whose `__module__` is that module is a
        subclass of `TextkitError`; it asserts that `textkit.cli.registry` was among them,
        which proves the recursion;
      - through the command line (a fake command, as in `tests/test_cli.py`): an
        `InvalidValueError` exits 1 with the message on stderr; a plain `ValueError`
        propagates out of `_main`.
      Every mention of `ValueError` as textkit's error in `textkit/`, `docs/`, `README.md`
      and `CHANGELOG.md` follows (`grep -rn ValueError` over them; the PR body lists the
      hits that remain and why, such as a standard-library `ValueError` that is caught). A
      task that merges after T3.2 applies the same sweep to its own files.
      `errors.py` defines classes only, so it has no README row; add the section
      `## Errors: \`textkit.errors\`` to `docs/usage.md`. CHANGELOG line: "Added
      `textkit.errors`: functions raise `InvalidValueError` instead of `ValueError`."
      Depends on T3.1 (both change the command line's error handling).
- [x] **T3.3 tokens with offsets** (medium): in `textkit/_tokens.py`, `words(text)` returns
      `list[Token]` instead of `list[str]`, where `Token` is a `typing.NamedTuple` with
      `text: str`, `start: int` and `end: int`, and `text_argument[start:end] == token.text`.
      Offsets come from the match itself (`re.finditer`), never from searching for the word.
      Every caller in `textkit/` and `tests/` follows (`word_count` stays
      `len(words(text))`; code that compares words compares `token.text`). Amend ADR 0002
      with a section "Offsets", placed before `## Cases` (the tests read everything after
      `## Cases` as case rows): offsets count code points, and combining marks stay inside
      their word. `tests/test_tokens.py` checks:
      - the offset invariant on every row of ADR 0002's case table;
      - offsets strictly increasing and not overlapping (`t[i].end <= t[i + 1].start`);
      - exact tokens for a repeated word (`"the cat the cat"`: the second `"the"` is
        `Token("the", 8, 11)`), after a character outside the BMP
        (`"\U0001F600 ab"` -> `[Token("ab", 2, 4)]`) and on NFD input
        written with escapes (`"cafe\u0301 x"` ->
        `[Token("cafe\u0301", 0, 5), Token("x", 6, 7)]`).
      No README row (a private module). CHANGELOG line:
      "`_tokens.words` returns tokens with their offsets."
- [x] **T3.4 template engine** (large): package `textkit/template/` with at least
      `lexer.py`, `parser.py` and `renderer.py`. Public function:
      `render(template: str, context: dict[str, Any]) -> str`.
      Syntax: `{{ expr }}` prints a value, where `expr` is a dotted name (`user.name`
      follows dict keys only) with optional filters (`{{ title | slug | truncate:20 }}`);
      `{% if expr %} ... {% else %} ... {% endif %}`, truth as Python's `bool`;
      `{% for item in expr %} ... {% endfor %}` over a list, with `loop.index` (from 1)
      inside (`loop` is the innermost loop and hides a context key named `loop`);
      `{# comment #}`; blocks nest; text outside tags is copied as is. Spaces inside the
      delimiters are optional (`{{x}}` is `{{ x }}`). Output is plain text: nothing is
      HTML-escaped; a `"\r\n"` in the template stays `"\r\n"` (tested through the
      subcommand too, with `_run_bytes`).
      Values: a value prints as `str(value)`, except `None`, which prints as `""`; filters
      apply to that string. Filters, a fixed table over the existing functions: `slug`
      (`slugify`), `snake`, `camel`, `kebab`, `squeeze`, `strip_accents`, `truncate:<width>`,
      and `upper` and `lower`.
      Errors (classes in `textkit/template/`, not in `__all__`; base class per the phase 3
      rule "Errors"): `TemplateError` with `line` and `column` (both from 1, columns in code
      points; a line ends after each `"\n"` only, so a `"\r"` is a column), and
      `TemplateSyntaxError(TemplateError)`, raised while parsing, for an
      unterminated `{{`, `{%` or `{#`, a block with no end tag, an unknown tag or filter, a
      bad filter argument (`truncate:` with a non-integer or a width below 3), and `else`,
      `endif` or `endfor` without their opening tag. Rendering raises `TemplateError` for a
      `for` over a value that is not a list, a dotted name through a value that is not a
      dict, and a missing name if the ADR says so. The position is that of the opening
      delimiter of the offending tag; for a block with no end tag, that of its opening tag.
      Write an ADR on names missing from the context (empty text or an error, and what `if`
      does with one); it ends with a table of cases (template, context -> output or error
      with its position) covering missing names, `None`, booleans and numbers, and the tests
      cover every row. A row is `template` (str), `context` (dict literal) and the outcome:
      the output (str) or `("<ErrorClassName>", line, column)`.
      Subcommand `python3 -m textkit render <template-file> <json-file>`, as
      `textkit/cli/render.py` (phase 3 rule "The command line"): writes the result; exit 1
      with `line:column: message` on stderr for any `TemplateError`; exit 2 for a file that
      cannot be read or is not a JSON object.
      Also `docs/template.md` (the syntax, every filter, every error), an example in
      `docs/usage.md`, the README row and the CHANGELOG line. At least 40 tests over the
      three modules, every error case with its line and column among them.
      PR after T3.1.
- [ ] **T3.5 Markdown to HTML** (large): package `textkit/markdown/` with at least
      `blocks.py`, `inlines.py` and `html.py`. Public function: `to_html(text: str) -> str`.
      Lines end at `"\n"`, `"\r\n"` or a lone `"\r"`; the ending is dropped before parsing
      (code block lines included) and every output line ends in `"\n"`.
      Blocks: ATX headings (`#` to `######` followed by a space); paragraphs (consecutive
      lines joined by one space); unordered lists (`-` or `*` followed by a space) and ordered
      lists (digits, `.` and a space; the numbers are not checked and no `start` attribute is
      written), one level, an item being its line plus the following lines indented by two
      spaces or more, joined by one space; fenced code blocks (three backticks, an optional
      language; an unclosed fence runs to the end of the text); block quotes (`>`, holding
      paragraphs only: the text after `>` is never parsed as another block); a horizontal
      rule (`---` alone on a line). A heading, a list item, a fence, a quote and `---`
      interrupt a paragraph; a blank line ends a list or a quote.
      Inlines: `**strong**`, `*em*`, `` `code` ``, `[text](url)`, and a backslash before
      `\`, `*`, `` ` ``, `[` or `]` to print it as is (not inside code spans: there a
      backslash is a character). An unmatched marker is printed as is. Raw HTML is never
      passed through: `&`, `<`, `>` and `"` are escaped everywhere, inside code too. A link
      URL whose scheme (the text before the first `:`, compared case-insensitively after
      removing whitespace and control characters) is not `http`, `https` or `mailto` is
      replaced by `#`; a URL with no scheme (relative) is kept.
      Output, exactly: `<h1>x</h1>`, `<p>a b</p>` and `<hr>` on one line each; `<ul>`, each
      `<li>…</li>` and `</ul>` on lines of their own (the same for `<ol>`); `<blockquote>`,
      each `<p>…</p>` and `</blockquote>` on lines of their own; a code block is
      `<pre><code class="language-x">` (`<pre><code>` with no language) followed directly by
      the escaped content lines as they are, then `</code></pre>`. Every line ends in `\n`
      and no other whitespace is added; `""` gives `""`.
      Write an ADR on what the subset leaves out, why raw HTML is escaped and why some link
      schemes are dropped; it ends with a table of cases (input -> output) with at least one
      row per block, per inline, per escape rule, a `javascript:` and a `JaVaScRiPt:` link,
      a heading and a fenced block with a language both with `"\r\n"` endings, and the tests
      cover every row.
      Subcommand `python3 -m textkit markdown <file>`, as `textkit/cli/markdown.py` (phase 3
      rule "The command line"): writes the HTML; exit 2 for a file that cannot be read; a
      file with `"\r\n"` endings is tested with `_run_bytes`.
      Also `docs/markdown.md` (every block and inline with an example), an example in
      `docs/usage.md`, the README row and the CHANGELOG line. At least 40 tests over the
      three modules.
      PR after T3.1.
- [x] **T3.6 line diff** (large): package `textkit/diff/` with at least `lcs.py`,
      `unified.py` and `patch.py`. Public functions:
      `unified_diff(a: str, b: str, context: int = 3) -> str`,
      `apply_patch(text: str, patch: str) -> str` and
      `diff_words(a: str, b: str) -> list[tuple[str, str]]`.
      `unified_diff` compares lines (split after each `"\n"`, which stays in its line; a
      `"\r"` is part of the line, as in `diff -u`) with its own longest common subsequence
      (no `difflib` in `textkit/`; ties broken by a rule the ADR states, deletions before
      insertions) and returns the unified format of GNU diffutils' `diff -u` (not the
      Apple/FreeBSD `diff` of macOS, which numbers an empty range at the top of a file 1,
      not 0): `--- a` and `+++ b`, then hunks `@@ -l,s +l,s @@` with `context` lines
      around each change, where `,s` is left out when `s == 1` and an empty range is `l,0`
      with `l` the line before it; two changes share a hunk when at most `2 * context`
      unchanged lines separate them; `""` when
      `a == b`; `context < 0` is rejected (phase 3 rule "Errors"). Write an ADR on a text
      that does not end in a newline (the `\ No newline at end of file` marker), the tie
      rule, and the time and memory the LCS takes (with the input size it is meant for).
      A table of at least 6 cases whose shortest edit is unique compares `unified_diff`
      byte for byte with the output of GNU `diff -u` (captured once with GNU diffutils, for
      example `gdiff` from Homebrew's `diffutils`, or `git diff --no-index`, which numbers
      the same way; pasted into the test, with its headers replaced by `--- a` and `+++ b`;
      a comment above the table names the tool and its version). The table includes a gap
      of exactly `2 * context` unchanged lines (one hunk), a gap of `2 * context + 1` (two
      hunks), a text without a final newline, and at `context=0` an insertion before line 1
      (`@@ -0,0 +1 @@`) and a deletion of line 1 (`@@ -1 +0,0 @@`). `docs/diff.md` and the
      ADR state that `apply_patch` reads GNU numbering, so a BSD `-1,0` hunk is applied after
      line 1.
      `apply_patch(a, unified_diff(a, b)) == b`: test it on a table of cases (an empty
      text, one line, no final newline on either side, a change in the first and in the
      last line, two hunks, two changes close enough to share a hunk) and on 200 random
      pairs from a seeded `random.Random`, whose lines are drawn from a small alphabet that
      includes a line ending in `"\r\n"` and texts without a final newline. `apply_patch`
      applies each hunk at its stated lines, with no fuzz, and raises `PatchError`
      (a class in `textkit/diff/`, not in `__all__`; base class per the phase 3 rule
      "Errors"), whose message contains the hunk's `@@` header, when a context or removed
      line does not match the text; input that is not a well-formed unified diff raises
      `PatchError` too. `""` is the empty patch and returns `text` unchanged; header lines
      are `--- ` and `+++ ` followed by anything (a file name, a timestamp, `a/` paths) and
      are ignored; headers with no hunk are malformed. Both are rows of the case table.
      `diff_words` returns `(op, word)` pairs, `op` being `"="`, `"-"` or `"+"`, over the
      words of `_tokens.words`, each word exactly as in its text, compared by
      `token.text` only (T3.3).
      Subcommand `python3 -m textkit diff <file-a> <file-b>`, as `textkit/cli/diff.py`
      (phase 3 rule "The command line"): writes the unified diff, its headers `--- a` and
      `+++ b` as `unified_diff` gives them; exit 0 when the files are equal (nothing
      written), 1 when they differ, 2 for a file that cannot be read. A file with `"\r\n"`
      endings against the same text with `"\n"` exits 1 and prints the `-`/`+` lines
      (tested with `_run_bytes`).
      Also `docs/diff.md` (the format, the three functions, the errors), examples in
      `docs/usage.md`, the README rows and the CHANGELOG lines. At least 40 tests over the
      three modules.
      PR after T3.1 and T3.3.
- [x] **T3.7 `dedent`** (small) in `textkit/strings.py`: `dedent(text) -> str` removes the
      prefix of spaces and tabs common to every non-blank line (no `textwrap`). Lines are
      split with `str.splitlines(keepends=True)` and their endings are kept as they are (so
      `"\x0c"` and `"\x85"` end a line too, unlike the `"\n"`-only rule of T3.4 and T3.6:
      the docstring says so and a test pins a `"\x0c"`). A
      line of spaces and tabs only does not count for the prefix and becomes empty (its line
      ending stays); a tab and a space are different characters; `""` gives `""`. Tests pin
      a text with no final newline, `"\r\n"` endings and a blank last line.
- [x] **T3.8 `center`** (small) in `textkit/strings.py`:
      `center(text, width, fill=" ") -> str` pads `text` on both sides to `width` code
      points; when the padding is odd, the extra `fill` goes on the right (so not
      `str.center`, which sometimes puts it on the left). A text of `width` or more is
      returned unchanged. `len(fill) != 1` or `width < 0` raises the phase 3 "Errors" error
      (`ValueError` before T3.2, `InvalidValueError` after), checked first,
      even when the text is longer than `width`. Tests pin `center("ab", 5) == " ab  "` (where
      `str.center` gives `"  ab "`) and `center("abc", 6) == " abc  "`.
      PR after T3.7 (see "Order").
- [x] **T3.9 `ngrams`** (small) in `textkit/counts.py`:
      `ngrams(text, n=2) -> list[tuple[str, ...]]`, the runs of `n` consecutive words
      (`_tokens.words`, each word its `token.text`, exactly as in the text), in order. Fewer
      than `n` words give `[]`; `n < 1` raises the phase 3 "Errors" error (`ValueError`
      before T3.2, `InvalidValueError` after). Depends on T3.3.
- [x] **T3.10 `levenshtein`** (small) in `textkit/strings.py`: `levenshtein(a, b) -> int`,
      the edit distance over code points (insert, delete, substitute, each of cost 1), with
      two rows of memory: a test with `tracemalloc` shows a peak under 1 MB for two strings
      of 1000 characters. `levenshtein("", s) == len(s)`; it is symmetric: test both.
      `levenshtein("kitten", "sitting") == 3`. PR after T3.8 (see "Order").
