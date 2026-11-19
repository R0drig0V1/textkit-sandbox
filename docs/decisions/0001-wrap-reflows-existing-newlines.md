<!-- ADR 0001: how textkit.strings.wrap treats line breaks already present in its input. -->
# 0001. `wrap` reflows existing newlines

## Context

`wrap(text, width)` (plan task T1.4) splits text into lines of at most `width` characters at
spaces and returns them as a list. The task leaves open what happens to line breaks already in
`text`. Two readings are reasonable:

1. **Hard breaks**: every existing line is wrapped on its own, and blank lines survive in
   some form (an empty string in the result, or nothing).
2. **Reflow**: line breaks are separators like spaces, and the whole text is re-packed.

Hard breaks keep the author's layout, but they force extra decisions with no obvious answer
(is a blank line an `""` element? do several blank lines collapse? does `"\r\n"` count once?),
and the result would no longer be "lines of the wrapped text" alone. The standard library's
`textwrap.wrap` reflows by default (`replace_whitespace=True`), so callers who know it expect
the same.

## Decision

`wrap` reflows. Before splitting, `"\r\n"`, `"\r"` and `"\n"` are each replaced by one
space; from then on they behave exactly like spaces: a run of them collapses to one
separator, and leading or trailing ones are dropped. No returned line contains a newline.

Only spaces and these line breaks separate words. Tabs, non-breaking spaces and other
whitespace are part of the word they touch, because the task says "at spaces" and splitting on
`str.split()`'s wider whitespace set would, for example, break text at a non-breaking space.

| Input | `width` | Result |
|-------|---------|--------|
| `"one\ntwo three"` | 20 | `["one two three"]` |
| `"a\r\nb\rc"` | 10 | `["a b c"]` |
| `"a\n\nb"` | 10 | `["a b"]` |
| `" \n \r\n "` | 5 | `[]` |
| `"a\tb c"` | 3 | `["a\tb", "c"]` |

## Consequences

- Paragraph structure is lost: `wrap("p1\n\np2", w)` joins the paragraphs. A caller who wants
  per-paragraph wrapping splits on blank lines first and calls `wrap` on each part.
- Every element of the result is a single line, so `"\n".join(wrap(text, w))` is always a
  valid wrapped rendering of `text`.
- Changing this later to hard breaks would change results for any input with newlines, so it
  would be a breaking change and needs a new ADR.
