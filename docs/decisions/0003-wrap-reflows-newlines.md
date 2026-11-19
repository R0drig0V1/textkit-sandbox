<!-- ADR 0003: what textkit.strings.wrap does with newlines already in its input. -->
# 0003. `wrap` treats existing newlines as word separators

## Context

`wrap(text, width) -> list[str]` (plan task T1.4) splits text into lines of at most `width`
characters at spaces, collapses runs of spaces and drops leading and trailing ones. The
plan leaves open what happens to newlines (and other whitespace) already in `text`. Two
readings are reasonable:

1. **Reflow:** a newline is just another separator, like a space. `"one\ntwo"` with a wide
   `width` gives `["one two"]`.
2. **Hard breaks:** a newline always ends a line; each input line is wrapped on its own, and
   blank lines become `""` entries (paragraphs survive).

## Decision

Reflow. Every whitespace character for which `str.isspace()` is true (space, `\n`, `\r`,
`\t`, form feed, no-break space, ...) separates words, and any run of them counts as one
separator. The implementation is `text.split()` followed by greedy packing.

Reasons:

- It keeps the task's guarantees simple and testable: each output line is words joined by
  single spaces, so no line ever contains `\n`, `\t` or a run of spaces, and `""` or
  whitespace-only input gives `[]` (with hard breaks, `"\n"` would have to give `[""]` or
  `["", ""]`, a rule of its own).
- It matches what callers expect from a wrap of free text, and Python's
  `textwrap.wrap`, whose default also turns whitespace into spaces.
- It is consistent with `squeeze`, which already uses `str.split()` to collapse whitespace.
- Wrapping is idempotent: `wrap("\n".join(wrap(t, w)), w) == wrap(t, w)`.
- Hard breaks are easy to build on top (`[l for p in text.split("\n") for l in wrap(p, w)]`),
  while reflow cannot be recovered from a hard-break `wrap`.

## Consequences

- Paragraph and line structure of the input is lost; a caller that wants to keep it splits
  the text first and wraps each part.
- Whitespace other than the ASCII space is also a separator, so `"a b"` wraps as two
  words; a no-break space does not glue words together.
- A different behaviour later (a `keep_newlines` flag, for instance) would be an addition
  with this behaviour as the default, not a change to it.
