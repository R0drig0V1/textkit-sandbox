<!-- ADR 0003: how textkit.strings.wrap treats newlines already present in its input. -->
# 0003. `wrap` treats existing newlines as spaces

## Context

`wrap(text, width)` (plan task T1.4) splits text into lines of at most `width` characters at
spaces, collapsing runs of spaces and dropping leading and trailing ones. The task leaves
open what happens to newlines already in `text`. The options were:

1. **Separator, like a space** (reflow): `"a\nb"` -> `["a b"]`. Paragraph breaks are lost.
2. **Hard break**: wrap each input line on its own and concatenate the results. Then it must
   be decided whether a blank line yields `""` in the output, which clashes with
   `wrap("", w) == []`, or vanishes, which loses the paragraph break anyway.
3. **Ordinary character**: a newline is part of the word it touches. Returned lines would
   then contain `"\n"`, and their printed width would no longer be their `len`.

## Decision

Option 1. Every character for which `str.isspace()` is true (`"\n"`, `"\r\n"`, `"\t"`,
`" "`, ...) separates words exactly like a space; the implementation is
`text.split()`. The text is reflowed, and no returned line contains a line break.

This matches the standard library's `textwrap.wrap` (its default `replace_whitespace=True`)
and textkit's own `squeeze`, keeps the result a plain list of lines with
`len(line) <= width` for every line that is not a single over-long word, and leaves no edge
case around blank lines.

## Consequences

- Paragraph structure is not preserved. A caller who needs it splits the text into
  paragraphs first (for example on blank lines) and wraps each one.
- Tabs and other Unicode whitespace are separators too, not only `" "`; a tab is never
  counted as part of a word's width.
- Changing this later (for example to hard breaks) changes the output for any input that
  contains a newline, so it would be a breaking change to `wrap`.

| Input | `width` | Output |
|-------|---------|--------|
| `"a\nb"` | 10 | `["a b"]` |
| `"one two\n\nthree"` | 7 | `["one two", "three"]` |
| `"a\r\nb\tc d"` | 20 | `["a b c d"]` |
| `"\n\n"` | 5 | `[]` |
