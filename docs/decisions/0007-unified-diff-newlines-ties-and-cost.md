<!-- ADR 0007: textkit.diff's unified format, its tie rule and its cost (plan task T3.6). -->
# 0007. `unified_diff`: missing final newlines, the tie rule and the cost of the LCS

## Context

Plan task T3.6 adds the package `textkit.diff`: `unified_diff(a, b, context=3)` writes the
unified format of GNU diffutils' `diff -u`, `apply_patch(text, patch)` applies it, and
`diff_words(a, b)` compares words. The plan forbids `difflib` in `textkit/`, so the package
computes its own longest common subsequence (`textkit/diff/lcs.py`), and it asks this ADR
to settle three things that a reader of the code would otherwise question:

1. how a text that does not end in a newline is written and read back;
2. which of several equally short edit scripts is chosen (two texts often have more than
   one longest common subsequence: `"p\nq\n"` and `"q\np\n"` share either line);
3. what the LCS costs in time and memory, and for which inputs it is meant.

It also records which line numbering `apply_patch` reads, since `diff` tools disagree.

## Decision

**Lines.** A line ends after each `"\n"` and keeps it; nothing else ends a line, so the
`"\r"` of `"\r\n"` is part of its line, as in `diff -u`, and a `"\r\n"` line differs from
the same line ending in `"\n"`. The last line has no `"\n"` when the text does not end in
one.

**A text without a final newline** is written as GNU diff writes it: the line is printed
with a `"\n"` added, and the next line is `\ No newline at end of file`. Its "no newline"
state is part of the line, so `"x"` and `"x\n"` are different lines: `"a\nx"` against
`"a\nx\n"` deletes `x` (with the marker) and inserts `x`. Every line of a diff therefore
ends in `"\n"`, and `apply_patch` removes the `"\n"` of a hunk line followed by a line
starting with `\` (any text after it, since translated `diff`s print the message in other
languages). `apply_patch` rejects a patch that would glue two lines together: lines added
after a last line with no newline, or a hunk whose new side ends without a newline before
the end of the text.

**The tie rule.** `lcs.edit_script` walks both sequences from the start, over a table of
LCS lengths of their suffixes, and at each step:

1. keeps `a[i]` and `b[j]` when they are equal (the earliest possible match);
2. otherwise deletes `a[i]` when that still leaves a longest common subsequence, and
   inserts `b[j]` only when deleting would lose one (deletions first);
3. finally reorders each run of changes between two kept items so that all its deletions
   come before all its insertions.

Rule 3 is also what the unified format shows (a hunk prints a change's `-` lines before its
`+` lines), and `diff_words` gives its pairs in the same order. The script stays a shortest
one: rules 1 and 2 never lose an LCS, and rule 3 keeps the same kept items. GNU diff uses a
different algorithm (Myers' with heuristics), so when the shortest edit is not unique the
two may put a change in a different place; `tests/test_diff_unified.py` therefore compares
with GNU only on cases whose shortest edit is unique.

**Cost.** The common prefix and suffix are matched first in linear time; the differing
middle, `n` lines of `a` against `m` lines of `b`, takes `O(n * m)` time and memory (one
table cell per pair of lines). Measured on Python 3.9, a middle of 1000 against 1000 lines
takes about 0.2 s and 8 MB; 2000 against 2000 about 0.8 s and 33 MB. `textkit.diff`
is meant for texts of up to a few thousand lines, where that is acceptable; it does not
switch to a linear-memory algorithm (Hirschberg's, Myers' linear space) for larger ones.
The same holds for `diff_words`, in words.

**Numbering.** Hunk headers follow GNU diff (and `git diff`): a range of `s` lines starting
at line `l` is `l,s`, `,s` is left out when `s == 1`, and an empty range is `l,0` with `l`
the line *before* it, so `-0,0` at the top of a file. The `diff` of macOS (Apple/FreeBSD)
writes `-1,0` there instead. `apply_patch` reads GNU numbering only, so a BSD `-1,0` hunk is
applied after line 1, not at the top; `docs/diff.md` says so. It applies each hunk exactly
at its stated old lines, with no fuzz, and does not check the `+l` start.

## Consequences

- `apply_patch(a, unified_diff(a, b)) == b` for every pair of texts, including texts with
  `"\r\n"` lines and without a final newline; the tests check it on 200 random pairs.
- The output equals GNU `diff -u` (headers aside) whenever the shortest edit is unique; for
  other inputs it is a valid, equally short diff that may place a change elsewhere.
- Changing the tie rule changes the output of `unified_diff` and `diff_words` for many
  inputs: it would be a breaking change, and this ADR has to change first.
- Large inputs that differ almost everywhere are slow and memory-hungry (quadratic); a
  caller with files of tens of thousands of lines should use GNU `diff`.
- Patches written by BSD `diff` with an insertion at the top of the file apply one line too
  low; patches from GNU `diff` and `git diff` apply as written.
