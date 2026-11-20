<!-- ADR 0003: how textkit.strings.wrap treats newlines already present in its input. -->
# 0003. `wrap` reflows text: existing newlines are separators like spaces

## Context

`wrap(text, width) -> list[str]` (plan task T1.4) splits text into lines of at most `width`
code points at spaces, collapses runs of spaces, drops leading and trailing spaces and never
keeps the separating space in a line. The plan leaves open what happens when the input
already contains newlines (`"one\ntwo three"`). Three readings are possible:

1. **Newlines are ordinary characters**, part of the word they touch. A returned line could
   then contain `"\n"`, so printing `"\n".join(wrap(...))` would give lines longer than
   `width`, and `len(line)` would no longer be the visible width. This breaks the purpose of
   the function.
2. **Newlines are hard breaks**: each input line is wrapped on its own and the results are
   concatenated. This keeps paragraphs, but needs more rules the plan does not give: does a
   blank line produce `""` in the result (which `wrap("", w) == []` suggests it should not),
   do `"\r\n"` and `"\r"` count, are several blank lines kept or collapsed.
3. **Newlines are separators like spaces**: the text is reflowed into one paragraph.

## Decision

Option 3. Every character for which `str.isspace()` is true (space, `\n`, `\r`, `\t`, and
other Unicode whitespace) separates words exactly as a space does; the implementation uses
`text.split()` with no argument. So `wrap("one\ntwo three", 20) == ["one two three"]`,
`wrap("a\n\nb", 20) == ["a b"]` and `wrap("a\r\nb\tc", 20) == ["a b c"]`.

## Consequences

- Every returned line contains no whitespace other than single spaces between words, so
  `len(line)` is its width and `"\n".join(wrap(text, w))` prints lines of at most `w`
  (except a single word longer than `w`, which gets its own line).
- The rule matches `squeeze`, which also treats all whitespace alike, and the default of the
  standard library's `textwrap.wrap` (`replace_whitespace=True`).
- Paragraph breaks are lost. A caller who wants to keep them splits first and wraps each
  paragraph: `[wrap(p, w) for p in text.split("\n\n")]`. Adding a keep-newlines mode later
  would be a new parameter with this behaviour as its default, so it is not a breaking
  change.
- Tests in `tests/test_strings.py` (`WrapTest`) pin the newline, `\r\n`, tab and
  whitespace-only cases.
