<!-- ADR 0003: how textkit.strings.wrap handles newlines already present in its input. -->
# 0003. `wrap` treats existing newlines as word separators

- Status: accepted
- Date: 2026-11-18
- Plan task: T1.4

## Context

`wrap(text, width) -> list[str]` (T1.4) splits text into lines of at most `width` characters
at spaces. The plan fixes the rules for spaces (runs collapse to one, leading and trailing
spaces are dropped, lines never contain the separating space) but not for newlines that are
already in `text`, such as `"first line\nsecond line"` or a blank line between paragraphs.

Two readings are possible:

1. **Hard breaks.** Each existing line is wrapped on its own and a newline always ends a
   line. This needs further rules the plan does not give: what a blank line becomes (an
   empty string in the list? dropped?), whether `"\r\n"` counts as one break, and whether
   trailing newlines produce empty lines.
2. **Separators.** A newline is whitespace between words, like a space; the text is
   re-flowed as one paragraph.

## Decision

Existing newlines are word separators, not kept. More generally, every character for which
`str.isspace()` is true (space, `\n`, `\r`, `\t`, and the other Unicode spaces) separates
words, and runs of them collapse exactly like runs of spaces. The implementation is
`text.split()` followed by greedy filling.

Consequences for callers, each covered by `WrapTest` in `tests/test_strings.py`:

| Input | `width` | Result |
|-------|---------|--------|
| `"a\nb"` | 80 | `["a b"]` |
| `"one\n\ntwo"` (blank line) | 80 | `["one two"]` |
| `"a\r\nb\tc"` | 80 | `["a b c"]` |
| `"aa\nbb\ncc"` | 5 | `["aa bb", "cc"]` |
| `"\n\n"` | 10 | `[]` |

No returned line contains a newline (or any other whitespace at either end).

## Consequences

- `wrap` is consistent with `squeeze`, which also treats all whitespace alike: the words of
  `wrap(t, w)` joined by single spaces equal `squeeze(t)`.
- The result has no empty strings and no ambiguity about blank lines, CRLF or trailing
  newlines; `wrap` of whitespace-only text is `[]`, like `wrap("", w)`.
- Paragraph structure is lost. A caller that wants to keep paragraphs splits on its own
  delimiter first (for example `text.split("\n\n")`) and wraps each part. If a
  paragraph-preserving mode is ever needed it should be a new function or an explicit
  keyword argument, not a change to this default; changing it would alter the output for
  every input that contains a newline.
