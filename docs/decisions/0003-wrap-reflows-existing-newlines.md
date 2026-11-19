<!-- ADR 0003: how textkit.strings.wrap treats line breaks already in its input (T1.4). -->
# 0003. `wrap` reflows existing newlines

## Context

`wrap(text, width) -> list[str]` (plan task T1.4) splits text into lines of at most `width`
characters at spaces, collapsing runs of spaces and dropping leading and trailing ones. The
plan leaves open what happens to line breaks the input already contains. The options were:

1. **Hard breaks**: wrap each input line on its own and keep its end as a line end. Blank
   lines (paragraph breaks) then have no faithful representation: either they vanish, which
   makes the option half-honest, or they become `""` items, which contradicts
   `wrap("", w) == []` and forces every caller to filter them.
2. **Reject**: raise `ValueError` on any newline. Safe but unhelpful: most text that needs
   wrapping arrived with line breaks of its own.
3. **Reflow**: treat a line break like a space. Re-wrapping already wrapped text to a new
   width, the most common reason to call `wrap` on multi-line input, then just works.

## Decision

Option 3. In `wrap`, `"\n"` and `"\r"` (so also `"\r\n"`) are word separators exactly like
`" "`: they break words, collapse with neighbouring spaces and breaks, and are dropped at
both ends. No line in the result contains a line break.

Only spaces and line breaks are break points. Other whitespace (tabs, non-breaking spaces,
other Unicode spaces) stays inside its word, as the task says "at spaces"; a non-breaking
space in particular must not become a break point.

## Consequences

- `wrap("one\ntwo three", 80) == ["one two three"]`; `wrap("a\n\nb", 80) == ["a b"]`;
  `wrap("\n\n", 5) == []`.
- Paragraph structure is lost. A caller who wants to keep paragraphs splits on blank lines
  first and wraps each paragraph, e.g. `[wrap(p, w) for p in text.split("\n\n")]`.
- `"a\tb"` is one word of three characters; callers who want tabs as separators normalise
  them first (for example with `squeeze`).
- Changing to hard breaks later would change results for any input with newlines, so it
  would need a new function or a flag, not a silent change.
