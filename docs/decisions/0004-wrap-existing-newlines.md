<!-- ADR: how textkit.strings.wrap treats newlines already in its input (plan task T1.4). -->
# 0004. `wrap` treats existing newlines as word separators

## Context

`wrap(text, width) -> list[str]` (T1.4) splits text into lines of at most `width` characters
at spaces. Its input may already contain line breaks (`\n`, `\r\n`, `\r`), for example a
paragraph copied from a file. There are two reasonable behaviours:

1. **Reflow**: a newline is just another separator, like a space. The text is re-wrapped as
   one paragraph.
2. **Preserve**: a newline is a hard break. Each input line (or each paragraph separated by
   blank lines) is wrapped on its own, and blank lines become `""` entries in the result.

Preserving would need extra rules nobody has asked for: whether a single `\n` or only a
blank line is a break, how many `""` entries a run of blank lines gives, whether trailing
newlines produce empty lines. It would also make "runs of spaces collapse" and "leading and
trailing spaces are dropped" mean something different per input line.

## Decision

`wrap` **reflows**. Every character for which `str.isspace()` is true, newlines included,
is a word separator. The implementation splits with `str.split()` (no argument), so runs of
whitespace collapse, leading and trailing whitespace is dropped, and the words are packed
greedily into lines joined by a single space.

This matches the standard library's `textwrap.wrap` default (which also replaces
whitespace) and keeps the result a plain list of lines: no returned line ever contains a
newline, so `"\n".join(wrap(text, w))` is always well formed.

| Input | `width` | Result |
|-------|---------|--------|
| `"one\ntwo three"` | 80 | `["one two three"]` |
| `"one\n\ntwo"` | 3 | `["one", "two"]` |
| `"a\r\nb\rc"` | 80 | `["a b c"]` |
| `"a\tb c"` | 80 | `["a b c"]` |
| `"para one\n\npara two\n"` | 4 | `["para", "one", "para", "two"]` |

## Consequences

- Paragraph structure is lost. A caller who wants paragraphs kept splits on blank lines
  first and calls `wrap` on each paragraph.
- Tabs and no-break spaces (`U+00A0`) are separators too, because `str.isspace()` is true
  for them. A caller who needs a non-breaking space must not rely on `U+00A0` to keep two
  words together.
- Changing to "preserve" later would change the output for any input with a newline, so it
  would be a breaking change of `wrap`, or a new parameter defaulting to the current
  behaviour.
