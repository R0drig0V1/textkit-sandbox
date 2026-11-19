<!-- ADR: how textkit.strings.wrap treats existing newlines and other whitespace. -->
# 0003. `wrap` reflows newlines and other whitespace like spaces

## Context

Plan task T1.4 defines `wrap(text, width) -> list[str]`: break at spaces into lines of at most
`width` characters, collapse runs of spaces, drop leading and trailing spaces, and give a
word longer than `width` a line of its own. It leaves open what happens to whitespace that is
not a plain space: newlines already in the text, `\r\n`, tabs, and the Unicode spaces. Two
readings are reasonable:

1. **Reflow.** Every whitespace character is a word separator. The input is one paragraph
   and its existing line breaks are discarded.
2. **Preserve.** Existing newlines are hard breaks. Each input line (or paragraph) is
   wrapped on its own, and empty lines come out as `""` entries.

The second reading raises more questions than it answers: does `"\n\n"` produce one or two
empty lines, are `\r\n` and `\r` both breaks, and does `wrap("", w) == []` still hold when the
input is `"\n"`? A function that returns `list[str]` also cannot tell the caller where the
paragraph boundaries were. `squeeze`, already in the same module, treats all whitespace as
one kind of separator.

## Decision

`wrap` **reflows**. The separators are every character for which `str.isspace()` is true
(space, `\t`, `\n`, `\r`, `\f`, `\v`, U+2003 EM SPACE, U+2028 LINE SEPARATOR, U+3000 and so on),
with three exceptions: the non-breaking spaces U+00A0 NO-BREAK SPACE, U+2007 FIGURE SPACE
and U+202F NARROW NO-BREAK SPACE. These three exist to forbid a break, so they are ordinary
characters of the word they are in (`"10\u00a0km"` is one word of length 5).

Consequences for callers:

- Existing newlines are dropped and do not force a break: `wrap("ab\ncd ef", 5)` ->
  `["ab cd", "ef"]`. Blank lines between paragraphs disappear too:
  `wrap("para one\n\npara two", 80)` -> `["para one para two"]`.
- Any run of separators, mixed or not (`" \t\n "`), counts as one. In the output, words are
  joined by exactly one ASCII space, so tabs never end up in a line.
- Whitespace-only input gives `[]`, the same as `""`.
- To keep paragraphs, split them first and wrap each one, for example
  `[wrap(p, w) for p in text.split("\n\n")]`.

The separator class is the regex `[^\S\u00a0\u2007\u202f]+`. For `str` patterns, `re`'s `\s`
matches exactly the characters for which `str.isspace()` is true (checked over all code points
under Python 3.9).

## Consequences

- The rule takes one sentence to state and leaves no edge cases about blank lines or line
  endings.
- Callers who want to keep line structure have to split the text themselves. If that need
  comes up, it should be a separate function or an explicit keyword argument added by a new
  ADR, not a change to this default.
- Tests in `tests/test_strings.py` (`WrapTest`) pin newlines, `\r\n`, tabs, `\f`, `\v`,
  Unicode spaces and the three non-breaking spaces.
