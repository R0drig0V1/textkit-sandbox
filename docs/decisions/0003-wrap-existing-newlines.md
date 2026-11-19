<!-- ADR 0003: how textkit.strings.wrap treats line breaks already in its input (plan task T1.4). -->
# 0003: `wrap` reflows text: existing line breaks separate words like a space

## Context

`wrap(text, width) -> list[str]` (T1.4) splits text into lines of at most `width` characters
at spaces. The plan pins spaces (runs collapse, ends dropped, `wrap("", w) == []`) but not
what happens to line breaks already in `text`. Three readings were possible:

1. **Reflow:** a line break is a separator like a space; the input's line structure is lost.
2. **Hard breaks:** each input line is wrapped on its own and the results concatenated, so
   every existing line break forces a new output line.
3. **Keep them inside words:** only `" "` separates, so `"a\nb"` is one 3-character word.

Option 3 returns lines containing `\n`, which breaks the point of returning a list of lines
and makes `len(line)` meaningless as a display width. Option 2 has to decide what a blank
input line becomes: dropping it loses paragraph breaks anyway, while keeping it as `""`
makes `wrap("\n", w) == ["", ""]` sit oddly next to `wrap("", w) == []` and turns runs of
newlines into runs of empty lines, unlike runs of spaces, which collapse.

## Decision

Option 1, reflow. A line break is any boundary `str.splitlines()` recognizes (`\n`, `\r\n`,
`\r`, `\v`, `\f`, `\x1c`-`\x1e`, `\x85`, ` `, ` `); each one separates words
exactly like `" "`, and runs mixing spaces and line breaks collapse to one separator. No
returned line contains a line break. This is also the default behaviour of the standard
library's `textwrap.wrap`, so it surprises the fewest callers.

Only `" "` and line breaks are separators. Tabs, no-break spaces (` `) and other
whitespace stay inside words: the plan says "at spaces", and a no-break space exists
precisely to stop a break.

## Consequences

- Paragraphs are not preserved. A caller that wants them splits first and wraps each one,
  e.g. `[wrap(p, w) for p in text.split("\n\n")]`.
- Text with no words, whatever mix of spaces and line breaks it has, gives `[]`.
- Changing to hard breaks later would change results for any input with a line break, so it
  would be a breaking change, not an extension.
- Tabs are counted as one character inside a word, not expanded; callers who need tab stops
  expand them first (`str.expandtabs`).

| Input | `width` | Result |
|-------|---------|--------|
| `"one\ntwo three"` | 80 | `["one two three"]` |
| `"one\n\ntwo"` | 80 | `["one two"]` |
| `"aa\nbb cc"` | 5 | `["aa bb", "cc"]` |
| `"a\r\nb\rc d"` | 80 | `["a b c d"]` |
| `"\n\n \r\n"` | 5 | `[]` |
| `"a\tb c"` | 3 | `["a\tb", "c"]` |
