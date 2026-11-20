<!-- ADR 0007: textkit.diff, the final newline, the tie rule and the LCS cost (plan task T3.6). -->
# 0007. `textkit.diff`: a missing final newline, the tie rule and the cost of the LCS

## Context

`textkit.diff` (plan task T3.6) has `unified_diff(a, b, context=3)`, which prints the unified
format of GNU `diff -u`, `apply_patch(text, patch)`, which applies it, and
`diff_words(a, b)`. The plan rules out `difflib`, so the package computes its own longest
common subsequence (LCS) in `textkit/diff/lcs.py`. Three things need a decision that a reader
of the output, or of `apply_patch`'s errors, would otherwise question:

1. A text need not end in `"\n"`. Lines are split after each `"\n"`, which stays in its line,
   so the last line of such a text is the only line without one. The output must tell
   `"a"` from `"a\n"`, and `apply_patch` must give back exactly one of them.
2. Two texts often have several longest common subsequences (`"a\nb\n"` against
   `"b\na\n"` keeps either line). Which one is kept decides which lines are printed as
   removed and added, and so the output; it must not depend on chance.
3. The classic LCS table takes time and memory proportional to the product of the two
   lengths. That is a limit on the input, and it must be stated.

GNU diffutils and the Apple/FreeBSD `diff` of macOS also differ on how they number an empty
range at the top of a text (`@@ -0,0 +1 @@` against `@@ -1,0 +1 @@`), which matters both for
the output and for reading patches.

## Decision

**A missing final newline** is written as GNU `diff` writes it: the line is printed, a
`"\n"` is added so the diff stays one line per line, and the next line is
`\ No newline at end of file`. The marker follows the line on whichever side it is: after a
`-` line, a `+` line or a context line (when neither text ends in `"\n"` and the last line
is unchanged). So `"a"` against `"a\n"` is a change (`-a`, the marker, `+a`): the two lines
differ. `apply_patch` reads the marker back and strips the `"\n"` from the line before it,
on the side or sides that line belongs to, and rejects a marker that does not follow a
line, follows another marker or marks an empty line. A `"\r"` is an ordinary character:
`"x\r\n"` and `"x\n"` differ, and the `"\r"` is printed as is.

**Numbering** is GNU's: a range is `l,s` with `l` from 1, `,s` left out when `s == 1`, and an
empty range is `l,0` with `l` the line before it (`0,0` at the top). `apply_patch` reads the
same numbering, so an empty old range `l,0` means "after line `l`". A hunk from BSD `diff`
numbered `-1,0` is therefore applied after line 1, not before it; `apply_patch` does not
guess which tool wrote a patch. It also ignores the start of the new range: the old range
alone says where a hunk goes, and there is no fuzz.

**The tie rule.** Among the shortest edit scripts, `lcs.edit_script` picks one by two steps:

1. Lines common to the start of both texts, then lines common to the end of what remains,
   are unchanged. (Keeping a common first or last line is never worse; GNU `diff` does the
   same. Start before end: `"x\ny\nx\n"` against `"x\n"` keeps the first `x`.)
2. Between them, a walk from the top keeps two equal lines as soon as it meets them (the
   earliest match). When the current lines differ, it deletes the line of `a` if a longest
   common subsequence is still possible without it, and inserts the line of `b` only when
   it is not: **deletions win ties**. So `"a\nb\n"` against `"b\na\n"` deletes `a`, keeps
   `b` and adds `a`.

A consequence of step 2 is that every run of changes lists its removed lines before its added
lines: once a line of `b` is inserted, the current line of `a` is in every remaining longest
common subsequence, so the walk keeps it before it deletes anything else. `unified_diff`
prints the script as is, and `diff_words` uses the same function over words.
`tests/test_diff_lcs.py` pins both steps.

GNU `diff` uses Myers' algorithm with heuristics, so on a text with several shortest scripts
the two may choose differently; both are correct diffs and `apply_patch` applies either.
The byte-for-byte comparison with GNU in `tests/test_diff_unified.py` uses only cases whose
shortest edit is unique.

**The cost.** Trimming the common start and end takes O(n + m). The lines left between them,
n' and m', fill a table of (n' + 1)(m' + 1) LCS lengths, so the time and the memory are
O(n' * m'). Lines are mapped to small integers first, so a long line costs one comparison
per pair, not one per character. On Python 3.9, two unrelated texts of 1000 lines take about
0.25 s and 8 MB, 2000 lines about 1 s and 33 MB; a 5000-line text with 10 scattered
one-line changes takes about 1.5 s (the trimming cannot help when the changes are spread
out). The package is meant for texts of up to a few thousand lines: configuration files,
documents, test fixtures. A linear-memory algorithm (Myers, or Hirschberg's LCS) would raise
that limit at the cost of more code; the plan review chose to state the cost instead.

## Consequences

- The output of `unified_diff` can be compared with GNU `diff -u` (and `git diff`) and fed to
  GNU `patch`, and `apply_patch(a, unified_diff(a, b)) == b` holds for every pair of texts,
  final newlines and `"\r"` included.
- Line-ending changes are visible: a file converted from `"\r\n"` to `"\n"` differs on every
  line, as it does for GNU `diff`.
- The output is deterministic, but on ambiguous inputs it may differ from GNU's choice of
  lines; tools that compare diffs as text should compare unique cases only.
- Patches written by BSD `diff` with an empty range at the top of a file are applied one line
  lower than BSD `patch` would; `docs/diff.md` says so.
- Large inputs are slow and use memory quadratically; a caller with texts of tens of
  thousands of lines needs another tool, or a change of algorithm (and of this ADR).
