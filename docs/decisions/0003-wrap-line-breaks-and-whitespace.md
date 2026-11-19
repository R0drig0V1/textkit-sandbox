<!-- ADR 0003: how textkit.strings.wrap treats existing line breaks and whitespace. -->
# 0003: `wrap` keeps existing line breaks and normalises whitespace inside a line

Status: accepted (T1.4)

## Context

`wrap(text, width) -> list[str]` (plan task T1.4) splits text into lines of at most `width`
characters at spaces, and a word longer than `width` gets a line of its own. The plan leaves
open what happens to the line breaks that `text` already has, and the same question comes up
for everything else that is not a plain single space between words: runs of spaces, leading
and trailing whitespace, tabs, empty text and a `width` that cannot hold anything.

The two usual answers for existing newlines are:

1. **Treat them as ordinary whitespace** (what `textwrap.wrap` does): the whole text is one
   paragraph and is re-flowed. Paragraphs and lists in the input are lost.
2. **Treat them as hard breaks**: each source line is wrapped on its own. The structure the
   author typed survives; a hard-wrapped input cannot be re-flowed into longer lines.

Callers of a small text helper usually pass text they want displayed in a narrower column
(a commit body, a CLI help paragraph, a list); losing the blank line between paragraphs or
merging list items into one line is the surprising result. Re-flowing a single paragraph is
still one call away: `wrap(squeeze(text), width)`.

## Decision

1. **Existing line breaks are hard breaks.** `text` is cut with `str.splitlines()`, so the
   boundaries are `\n`, `\r\n` (one break, not two), `\r`, and the other line separators
   `splitlines` knows (`\v`, `\f`, `\x1c`-`\x1e`, `\x85`, `\u2028`, `\u2029`). Each
   source line is wrapped independently; no output line joins words from two source lines.
   We reuse `splitlines` rather than our own list so the rule is the standard library's,
   documented and stable.
2. **A final line break adds nothing**: `"a\n"` gives `["a"]` (the `splitlines` rule).
3. **A source line with no words gives exactly one `""`.** Blank lines, and lines of only
   whitespace, are kept as empty strings: `"a\n\nb"` gives `["a", "", "b"]`, and
   `"\n".join(wrap(text, w))` keeps the paragraph layout. Consecutive blank lines are each
   kept; they are not collapsed.
4. **Inside a line, any run of whitespace is one separator** (`str.split()` with no
   argument: spaces, tabs and other Unicode whitespace). Consequently:
   - runs of spaces collapse: `"a    b"` gives `["a b"]`;
   - leading and trailing whitespace of each line is dropped: `"  a b  "` gives `["a b"]`;
   - tabs separate words exactly like a space and are **not expanded** to columns:
     `"a\tb"` gives `["a b"]`;
   - words in an output line are joined by exactly one space.
5. **Greedy filling**: a line takes words while the joined length stays `<= width`. Length is
   `len()`, i.e. code points, not display columns (wide CJK characters and combining marks
   are not measured specially).
6. **A word longer than `width` is not broken.** It goes on a line of its own, which is then
   longer than `width`; the words around it go on the lines before and after.
7. **Empty text gives `[]`** (there are no lines). Whitespace-only text on one line gives
   `[""]` (one line with no words), following rule 3.
8. **`width <= 0` raises `ValueError`**, checked before anything else, so `wrap("", 0)` also
   raises. A width of 0 or less cannot hold any character, and silently returning one word
   per line would hide the caller's bug.

## Consequences

- Paragraphs, lists and blank lines in the input survive wrapping; callers that want a
  single re-flowed paragraph call `wrap(squeeze(text), width)`.
- Callers that do not want empty strings filter them: `[l for l in wrap(t, w) if l]`.
- Exact whitespace is not preserved (indentation, alignment with tabs or multiple spaces);
  `wrap` is not suitable for code or pre-formatted text.
- The only output line longer than `width` is a line holding a single over-long word, so
  `all(len(l) <= width or " " not in l for l in wrap(t, width))` always holds.
- Measuring code points keeps the function dependency-free and predictable, at the cost of
  misaligned columns for wide or combining characters.
- `tests/test_strings.py` (`WrapTest`) has one test per rule above.
