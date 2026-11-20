<!-- Reference of textkit.diff (plan task T3.6): the unified format it writes and reads, its
three functions and its errors. The decisions behind it are in ADR 0007. -->
# `textkit.diff`: line and word diffs

`textkit.diff` compares two texts line by line and writes the difference in the unified
format of GNU diffutils' `diff -u`; it applies such a diff back to a text; and it compares
two texts word by word. It uses its own longest common subsequence (`textkit/diff/lcs.py`,
no `difflib`). The choices behind it (a text without a final newline, the tie rule, the
cost) are in [ADR 0007](decisions/0007-unified-diff-newlines-ties-and-cost.md).

| Function | Module | |
|----------|--------|---|
| `unified_diff(a, b, context=3) -> str` | `textkit/diff/unified.py` | the unified diff of two texts |
| `apply_patch(text, patch) -> str` | `textkit/diff/patch.py` | applies a unified diff to a text |
| `diff_words(a, b) -> list[tuple[str, str]]` | `textkit/diff/words.py` | a word-by-word diff |

All three are imported from the package: `from textkit.diff import unified_diff`.

## Lines

A line ends after each `"\n"`, which belongs to it. Nothing else ends a line: the `"\r"` of
`"\r\n"` is part of its line, so `"a\r\n"` and `"a\n"` are different lines (as in
`diff -u`); `"\x0c"` and `"\x85"` are ordinary characters too, unlike `str.splitlines`. The
last line of a text that does not end in `"\n"` has no `"\n"`, and is therefore a
different line from the same text with one.

## The format

```
--- a
+++ b
@@ -2,4 +2,4 @@
 two
-three
+THREE
 four
 five
```

- Two header lines, always `--- a` and `+++ b` (`unified_diff` has no file names).
- Then one **hunk** per group of changes. Its header `@@ -l,s +l,s @@` gives, for the old
  text (`-`) and the new one (`+`), the first line of the range (counted from 1) and its
  size. `,s` is left out when the size is 1 (`@@ -3 +3 @@`).
- An **empty range** (a hunk that only inserts, or only deletes) is `l,0` with `l` the line
  *before* the range: `@@ -0,0 +1 @@` inserts at the top of the file, `@@ -1 +0,0 @@`
  deletes line 1. This is GNU numbering, which `git diff` follows too. The `diff` of macOS
  (Apple/FreeBSD) numbers an empty range at the top of a file `1,0` instead.
- Each hunk line starts with `" "` (unchanged), `"-"` (only in the old text) or `"+"` (only
  in the new one). In a run of changes, all `-` lines come before the `+` lines.
- A hunk shows up to `context` unchanged lines (3 by default) before and after its changes.
  Two changes **share a hunk** when at most `2 * context` unchanged lines separate them;
  with one line more, they are two hunks.
- A line with no `"\n"` (the last line of a text without a final newline) is printed with a
  `"\n"` and followed by the line `\ No newline at end of file`.
- Every line of a diff ends in `"\n"`. Two equal texts give `""`, with no headers.

## `unified_diff(a, b, context=3)`

Returns the unified diff that turns `a` into `b`, as above. The kept lines are a longest
common subsequence of the two texts, so the diff is as short as possible; when several are,
the tie rule of ADR 0007 picks one (the earliest match; a deletion before an insertion).
On every input whose shortest edit is unique, the output is byte for byte that of GNU
`diff -u` with its headers replaced by `--- a` and `+++ b`
(`tests/test_diff_unified.py` holds the comparison table).

Cost: the common prefix and suffix are cheap; the differing middle takes `O(n * m)` time
and memory in its numbers of lines (about 0.2 s and 8 MB for 1000 against 1000 lines). It
is meant for texts of up to a few thousand lines.

Errors: `TypeError` if `a` or `b` is not a `str` or `context` is not an `int` (`bool`
included); `textkit.errors.InvalidValueError` if `context < 0`, even when the texts are
equal.

## `apply_patch(text, patch)`

Returns `text` with `patch` applied; `apply_patch(a, unified_diff(a, b)) == b` for any two
texts. What it reads:

- `""` is the empty patch: `text` comes back unchanged.
- Optional header lines `--- ` and `+++ ` (in that order) followed by anything: a file
  name, a timestamp, `a/` and `b/` paths. They are ignored. Headers with no hunk after them
  are malformed.
- Then one or more hunks in text order. Their numbers are ASCII digits (`0`-`9`). Text
  after the closing `@@` of a hunk header (git writes the enclosing function there) is
  ignored.
- A line starting with `\` right after a hunk line removes that line's `"\n"` (any text
  may follow the `\`: translated `diff`s print the message in other languages).
- Every line of the patch must end in `"\n"`.

How it applies a hunk:

- **GNU numbering.** `-l,s` with `s > 0` means lines `l` to `l + s - 1`; `-l,0` means
  "after line `l`" (`-0,0`: at the top). So a hunk written by BSD `diff` as `-1,0`, meant as
  "at the top", is applied **after line 1**. The `+l` start of a header is not checked; the
  sizes are, against the hunk's lines.
- **No fuzz.** A hunk applies exactly at its stated lines: every context and removed line
  must equal the text's line there, `"\r"` and the final newline included. There is no
  search for the lines elsewhere.

Errors: `TypeError` if `text` or `patch` is not a `str`; `PatchError` (below) otherwise.

## `diff_words(a, b)`

Returns `(op, word)` pairs in text order: `("=", w)` for a word in both texts, `("-", w)`
for a word only in `a`, `("+", w)` for a word only in `b`. The words are those of
`word_count` ([ADR 0002](decisions/0002-word-count-what-counts-as-a-word.md)): whitespace
and punctuation between them are neither compared nor returned. Each word is exactly as in
its text (no case folding, no normalization), so `"The"` against `"the"` is a change. The
same LCS and tie rule as `unified_diff` apply, in words.

Errors: `TypeError` if `a` or `b` is not a `str`.

## Errors

`PatchError` (`from textkit.diff import PatchError`) is raised by `apply_patch` when:

- the patch is not a well-formed unified diff: headers with no hunk, a `--- ` line not
  followed by `+++ `, a line where a hunk header was expected (non-ASCII digits included), a
  hunk whose lines do not add up to the sizes in its header (one line too many names that
  hunk), a hunk line that does not start with `" "`, `"-"` or
  `"+"`, a line after a `\ No newline at end of file` on the same side, a hunk with no
  lines, a non-empty old range at line 0, or a last line without `"\n"`;
- a hunk does not fit the text: a context or removed line differs from the text's line, the
  hunk goes past the end of the text, it overlaps or comes before the previous hunk, or it
  would glue two lines together (lines added after a last line with no newline, or a new
  last line without a newline before the end of the text).

When one hunk is at fault, the message contains its `@@` header, and for a mismatch the
line number and both lines:

```
hunk @@ -1,3 +1,3 @@ does not match line 3: expected 'x\n', found 'c\n'
```

`PatchError` subclasses `textkit.errors.InvalidValueError` (phase 3 rule "Errors"), so
`except TextkitError` catches it and it is not a `ValueError`; a `ValueError` from the
standard library inside `apply_patch` is turned into a `PatchError`. `InvalidValueError`
for a negative `context` and `TypeError` for a wrong argument type are not `PatchError`s.

## Command line

```sh
python3 -m textkit diff <file-a> <file-b>
```

Writes `unified_diff` of the two files (headers `--- a` and `+++ b`) to stdout. The files
are read as UTF-8 with no newline translation, so a file with `"\r\n"` endings differs from
the same text with `"\n"`. Exit 0 when the files are equal (nothing is written), 1 when they
differ, 2 when a file cannot be read or is not valid UTF-8
(`python3 -m textkit diff: error: <path>: <reason>` on stderr).
