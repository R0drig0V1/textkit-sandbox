<!-- ADR 0003: how textkit.strings.wrap handles newlines already in its input. -->
# 0003. `wrap` treats existing newlines as spaces

## Context

`wrap(text, width)` (plan task T1.4) splits text into lines of at most `width` characters at
spaces, collapsing runs of spaces and dropping leading and trailing ones. The plan leaves
open what happens to newlines already in `text`. The two reasonable readings are:

1. **Reflow**: a newline is whitespace like any other; the whole text is one paragraph.
2. **Preserve**: each existing line (or paragraph) is wrapped on its own and the breaks are
   kept, which raises follow-up questions: are blank lines kept as `""` entries, do `\r\n`
   and a lone `\r` count, are other whitespace characters (tabs) kept inside words.

## Decision

Reflow. Every whitespace character (`str.isspace()`: space, `\n`, `\r`, `\t`, and the rest)
separates words exactly like a space, and runs of any mix of them collapse. The
implementation tokenizes with `str.split()` with no argument.

| Input | `width` | Result |
|-------|---------|--------|
| `"a\nb"` | 10 | `["a b"]` |
| `"one\ntwo\n\nthree\tfour"` | 9 | `["one two", "three", "four"]` |
| `"  \n\t "` | 5 | `[]` |

## Consequences

- One rule covers spaces, tabs and every newline convention; `wrap` never returns `""`
  entries and no line contains whitespace other than single separating spaces.
- It matches the default of the standard library's `textwrap.wrap`
  (`replace_whitespace=True`), so the behaviour is unsurprising.
- Paragraph structure is lost. A caller who wants to keep it splits the text into
  paragraphs first and calls `wrap` on each; changing `wrap` itself to preserve breaks
  later would change its output for existing callers, so it would need a new ADR.
