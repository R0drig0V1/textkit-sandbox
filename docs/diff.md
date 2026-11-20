<!-- The textkit.diff package (plan task T3.6): the format, the three functions, the errors. -->
# Line and word differences: `textkit.diff`

`textkit.diff` compares texts line by line and word by word, with a longest common
subsequence of its own (`textkit/diff/lcs.py`; `difflib` is not used). The choices behind it,
a missing final newline, the tie rule and the cost, are in
[ADR 0007](decisions/0007-unified-diff-newlines-ties-and-cost.md). Runnable examples are in
the [usage guide](usage.md#diff-textkitdiff).

| Function | Module | Returns |
|----------|--------|---------|
| `unified_diff(a: str, b: str, context: int = 3) -> str` | `unified.py` | the unified diff from `a` to `b`, GNU `diff -u` format |
| `apply_patch(text: str, patch: str) -> str` | `patch.py` | `text` with a unified diff applied |
| `diff_words(a: str, b: str) -> list[tuple[str, str]]` | `words.py` | `(op, word)` pairs over the words of both texts |

`PatchError` (`patch.py`) is importable as `from textkit.diff import PatchError`; it is not in
`__all__`, which lists functions only. It subclasses `textkit.errors.InvalidValueError`, so
`except TextkitError` catches it, and it is not a `ValueError` (ADR 0006).

## Lines

A line ends after each `"\n"`, and the `"\n"` belongs to its line. Nothing else ends a line:
a `"\r"` (alone or before `"\n"`), a form feed or a Unicode line separator is a character of
its line, so `"x\r\n"` and `"x\n"` are different lines, as they are for `diff -u`. The last
line of a text that does not end in `"\n"` has no `"\n"`; `""` has no lines.

## The format

`unified_diff(a, b)` returns `""` when `a == b`. Otherwise it is the unified format of GNU
diffutils' `diff -u`:

```
--- a
+++ b
@@ -1,4 +1,4 @@
 first line
-removed line
+added line
 unchanged line
 last line
```

- The headers are always `--- a` and `+++ b`: the function has texts, not file names.
- A hunk header is `@@ -l,s +l,s @@`, the old range then the new one. `l` is the first line
  of the range, counted from 1, and `s` its length. `,s` is left out when `s == 1`
  (`@@ -3 +3 @@`). An empty range is `l,0` with `l` the line **before** it, so an insertion
  at the top of a text is `@@ -0,0 +1 @@` and a deletion of line 1 at `context=0` is
  `@@ -1 +0,0 @@`. This is GNU's numbering; the Apple/FreeBSD `diff` of macOS writes `1,0`
  for an empty range at the top instead.
- Each line of a hunk is a prefix and the line: `" "` for a context (unchanged) line, `"-"`
  for a line of `a` only, `"+"` for a line of `b` only. In a run of changes the `-` lines
  come first.
- A hunk has up to `context` unchanged lines before its first change and after its last one
  (fewer at the edges of the text). Two changes share a hunk when at most `2 * context`
  unchanged lines separate them; with `2 * context + 1` or more they are in two hunks.
- A line without a final `"\n"` is printed with one added and followed by the line
  `\ No newline at end of file`, whether it is removed, added or context.
- When several shortest diffs exist, the tie rule of ADR 0007 picks one: common first and
  last lines are kept, then the earliest match, and deletions win ties.

`tests/test_diff_unified.py` compares the output byte for byte with GNU numbering (captured
with `git diff --no-index`, which numbers as GNU does) on a table of cases with a unique
shortest edit.

Cost: O(n' * m') time and memory, n' and m' being the lines left after the common first and
last lines; about 1 s and 33 MB for two unrelated 2000-line texts. Meant for texts of up to a
few thousand lines (ADR 0007).

## Applying a patch

`apply_patch(text, patch)` reads the format above and returns the patched text, so
`apply_patch(a, unified_diff(a, b)) == b` for any `a` and `b`.

- `""` is the empty patch: the text comes back unchanged.
- Otherwise the patch starts with a `--- ` line and a `+++ ` line. Whatever follows `--- `
  and `+++ ` (file names, timestamps, `a/` and `b/` paths) is ignored. They must be followed
  by at least one hunk; a patch for a second file (another `--- ` line) is not accepted.
- Text after the second `@@` of a hunk header, after a space (a section heading, as `git
  diff` and `diff -p` write), is ignored.
- A hunk is applied exactly at the old range its header states, with **no fuzz**: every
  context and removed line must equal the text's line at that place, `"\r"` and final
  newline included. The new range's line count is checked against the hunk's lines; its
  start is not used.
- Empty ranges are read with **GNU numbering**: `l,0` means "after line `l`". A hunk written
  by BSD `diff` as `@@ -1,0 +1 @@` (an insertion at the top) is therefore applied after
  line 1.
- Hunks must come in order and must not overlap.

## Words

`diff_words(a, b)` returns `(op, word)` pairs: `("=", word)` for a word in both texts,
`("-", word)` for a word of `a` only and `("+", word)` for a word of `b` only, in order. The
words are those of the word rule of
[ADR 0002](decisions/0002-word-count-what-counts-as-a-word.md) (`textkit._tokens.words`, what
`word_count` counts), each exactly as it appears in its text, compared by its text alone:
case, accents and normalization count, and whitespace and punctuation between words are not
compared and not returned. The tie rule is the same as for lines.

## Errors

| Function | Error | When |
|----------|-------|------|
| `unified_diff` | `InvalidValueError` | `context` is negative |
| `apply_patch` | `PatchError` (an `InvalidValueError`) | the patch is malformed: no `--- `/`+++ ` headers, headers with no hunk, a bad hunk header (non-ASCII digits, or a number too long for `int`, included), a non-empty range starting at line 0, a hunk with two empty ranges, fewer or more lines than its header states, a line with an unknown prefix (an empty line included), a patch line without a final newline, a misplaced `\` line |
| `apply_patch` | `PatchError` | the patch does not apply: a context or removed line differs from the text, a range runs past the end of the text, hunks out of order or overlapping, or a line without a newline that would not be the last one |
| all three | `TypeError` | an argument of the wrong type (`context` must be an `int`, not a `bool`) |

When a hunk is at fault, the message of `PatchError` contains its `@@` header line (and, for a
mismatch, the line number and the expected and found lines).

## Command line

`python3 -m textkit diff <file-a> <file-b>` (`textkit/cli/diff.py`) prints
`unified_diff(a, b)` of the two files, read as UTF-8 with no newline translation, so a file
with `"\r\n"` endings differs from the same text with `"\n"` endings. Exit 0 when the files
are equal (nothing is printed), 1 when they differ, 2 when a file cannot be read or is not
valid UTF-8 (`python3 -m textkit diff: error: <path>: <reason>` on stderr).
