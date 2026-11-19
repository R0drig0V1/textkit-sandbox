<!-- ADR 0003: what wrap (plan task T1.4) does with the newlines and other whitespace already in its input. -->
# 0003. `wrap` reflows: existing newlines are break points, not kept

## Context

`wrap(text, width)` (plan task T1.4) splits text into lines of at most `width` characters at
spaces. The plan pins spaces (runs collapse to one, ends are dropped, no line holds the
separating space, a word longer than `width` gets its own line) but not the newlines, tabs and
other whitespace that the input may already contain. `"first line\nsecond"` could come back as
two lines or reflowed into one, and `"a\n\nb"` could keep or lose its blank line. The answer
changes the output of every multi-line input, so it is fixed here.

Options considered:

- **Hard breaks**: each input line is wrapped on its own and the results are concatenated.
  Keeps the author's line structure, but then a blank line must become `""` in the output,
  which clashes with the pinned rules: `wrap("", w) == []` and dropped leading/trailing
  spaces mean `"   "` gives `[]`, so `"\n"` giving `[""]` would be a special case. It also
  re-wraps text that was already wrapped at a different width into ragged short lines
  (`"aaaa bbbb\ncccc"` at width 20 would stay two lines).
- **Paragraphs**: blank lines separate paragraphs, single newlines are spaces. Useful, but it
  needs a way to show the paragraph break in a `list[str]` (an empty string element), the
  same special case as above, plus rules for `"\r\n"` and whitespace-only lines.
- **Reflow** (chosen): every ASCII whitespace character, newlines included, is a break point
  exactly like a space. This is what `textwrap.wrap` in the standard library does by default,
  so it is the least surprising choice for a Python user, and it needs no special case.

## Decision

`wrap` reflows its input as a single paragraph:

1. **Break points** are the ASCII whitespace characters: space, `\t`, `\n`, `\r`, `\v`, `\f`
   (the set `textwrap` uses). A run of them, of any mix, counts as one break point. So
   existing newlines (`\n`, `\r\n`, blank lines) are not kept: they separate words like a
   space and disappear from the output.
2. **Non-ASCII whitespace is not a break point.** The no-break space (U+00A0) exists to forbid
   a break, so it stays inside its word; the same holds for other Unicode spaces and for
   U+2028 LINE SEPARATOR. This differs from `str.split()` (and from `squeeze`, which collapses
   all Unicode whitespace).
3. **Filling is greedy**: a word goes on the current line if the line plus one space plus the
   word fits in `width` (counted in code points, `len`), else it starts a new line. Words are
   never cut; one longer than `width` gets a line of its own.
4. Whitespace-only text gives `[]`, the same as `""`.

Callers who want to keep paragraphs split them first and wrap each one:
`[line for p in text.split("\n\n") for line in wrap(p, width)]`.

## Consequences

- `wrap` has no special case for blank lines and never returns an empty string element: every
  line it returns is non-empty and has no leading, trailing or doubled space.
- Text that was already wrapped can be re-wrapped to a new width without ragged lines.
- Line structure in the input (poems, lists, code) is lost; that is the price of the choice,
  and the paragraph recipe above is the workaround.
- The table below is the contract. `tests/test_strings.py` reads it from this file and checks
  every row against `wrap`, so the table and the code cannot drift apart. Changing the rule
  means changing this ADR, its table and the tests in one PR.

## Cases

Inputs and outputs are Python literals; Output is `wrap(input, width)`.

| Input | Width | Output | Case |
|-------|-------|--------|------|
| `""` | 5 | `[]` | empty text |
| `"   "` | 5 | `[]` | spaces only |
| `"\n\n"` | 5 | `[]` | newlines only |
| `" \t\r\n "` | 5 | `[]` | mixed whitespace only |
| `"one two"` | 7 | `["one two"]` | line exactly `width` long |
| `"one two"` | 6 | `["one", "two"]` | separating space is in neither line |
| `"a   b"` | 10 | `["a b"]` | run of spaces collapses to one |
| `"  a b  "` | 10 | `["a b"]` | leading and trailing spaces dropped |
| `"a\nb"` | 10 | `["a b"]` | newline is a break point, not kept |
| `"a\r\nb"` | 10 | `["a b"]` | Windows newline is a break point |
| `"a\n\nb"` | 10 | `["a b"]` | blank line (paragraph break) is not kept |
| `"a\tb"` | 10 | `["a b"]` | tab is a break point |
| `"one\ntwo"` | 3 | `["one", "two"]` | newline where a break falls anyway |
| `"aaaa bbbb\ncccc"` | 20 | `["aaaa bbbb cccc"]` | wrapped text is reflowed |
| `"\nab cd\n"` | 2 | `["ab", "cd"]` | newlines at both ends dropped |
| `"a b c"` | 3 | `["a b", "c"]` | no-break space is not a break point |
| `"the quick brown fox"` | 10 | `["the quick", "brown fox"]` | greedy filling |
| `"abcdefghij xy"` | 5 | `["abcdefghij", "xy"]` | word longer than `width` gets its own line |
| `"a b c"` | 1 | `["a", "b", "c"]` | width 1 |
