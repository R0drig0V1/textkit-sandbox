<!-- Guide to textkit.markdown (plan task T3.5): every block and inline of the subset with an
example. Every ">>>" line is run by tests/test_markdown.py through doctest. Keep a blank line
before each closing fence: doctest reads expected output up to the first blank line. -->
# Markdown to HTML: `textkit.markdown`

`to_html(text: str) -> str` converts a small subset of Markdown to HTML, using the standard
library only. It is safe by construction: raw HTML is never passed through, and links to
schemes other than `http`, `https` and `mailto` are dropped. The reasons, and what the
subset leaves out, are in
[ADR 0007](decisions/0007-markdown-subset-escaping-and-link-schemes.md), which ends with a
table of cases that the tests check row by row.

The examples print the HTML, so each output line shows as it is written:

```pycon
>>> from textkit.markdown import to_html
>>> to_html("# Title")
'<h1>Title</h1>\n'
>>> to_html("")
''

```

## Lines

A line ends at `"\n"`, `"\r\n"` or a lone `"\r"`; the ending is dropped before parsing,
code blocks included, and every line of the output ends in `"\n"`. "Blank" means spaces and
tabs only. Block markers count only at the start of a line, with no indentation.

```pycon
>>> to_html("# Title\r\nline\rnext\r\n") == to_html("# Title\nline\nnext\n")
True

```

## Blocks

The HTML is written one element per line, with no other whitespace added. Blank lines
separate blocks and produce nothing.

**Headings**: `#` to `######`, then a space. The text is stripped of spaces at both ends;
closing `#`s are not removed. Without the space, or with seven `#`, the line is text.

```pycon
>>> print(to_html("## Section\n#hashtag"), end="")
<h2>Section</h2>
<p>#hashtag</p>

```

**Paragraphs**: consecutive lines, each stripped, joined by one space. A heading, a list
item, a fence, a quote or a `---` line interrupts a paragraph without a blank line.

```pycon
>>> print(to_html("one\n  two\n\nthree\n# Heading"), end="")
<p>one two</p>
<p>three</p>
<h1>Heading</h1>

```

**Unordered lists**: items start with `-` or `*` and a space (the two mix in one list).
An item is its line plus the following lines indented by two spaces or more, joined by one
space. Lists have one level: an indented `- b` is text of the item above. A blank line, or
any other line, ends the list.

```pycon
>>> print(to_html("- one\n  more\n* two\n  - not nested\nafter"), end="")
<ul>
<li>one more</li>
<li>two - not nested</li>
</ul>
<p>after</p>

```

**Ordered lists**: digits, `.` and a space. The numbers are not checked and no `start`
attribute is written.

```pycon
>>> print(to_html("3. three\n1. one"), end="")
<ol>
<li>three</li>
<li>one</li>
</ol>

```

**Fenced code blocks**: three backticks and an optional language (the first word after
them), up to a line of three backticks alone. An unclosed fence runs to the end of the
text. The content lines are written as they are, only escaped, right after the opening tag.

```pycon
>>> print(to_html("```python\nif a < b:\n    pass\n```"), end="")
<pre><code class="language-python">if a &lt; b:
    pass
</code></pre>
>>> print(to_html("```\nno language, no end"), end="")
<pre><code>no language, no end
</code></pre>

```

**Block quotes**: lines starting with `>`. A quote holds paragraphs only: the text after
`>` is never another block. A `>` line with no text separates paragraphs; a blank line, or
a line without `>`, ends the quote.

```pycon
>>> print(to_html("> # not a heading\n> same paragraph\n>\n> second"), end="")
<blockquote>
<p># not a heading same paragraph</p>
<p>second</p>
</blockquote>

```

**Horizontal rule**: `---` alone on a line.

```pycon
>>> print(to_html("above\n---\nbelow"), end="")
<p>above</p>
<hr>
<p>below</p>

```

## Inlines

Inlines are parsed in headings, paragraphs, list items and quote paragraphs, after their
lines are joined.

**Strong and emphasis**: `**strong**` and `*em*`, which nest. The opening marker must be
followed, and the closing one preceded, by a character that is not whitespace, so
arithmetic stays text.

```pycon
>>> print(to_html("**bold *and italic***, 2 * 3 * 4"), end="")
<p><strong>bold <em>and italic</em></strong>, 2 * 3 * 4</p>

```

**Code spans**: a backtick, one or more characters, a backtick. Inside, nothing is parsed
and a backslash is an ordinary character.

```pycon
>>> print(to_html(r"Run `ls *.py` or `a\*b`"), end="")
<p>Run <code>ls *.py</code> or <code>a\*b</code></p>

```

**Links**: `[text](url)`. The text is parsed as inlines; the URL runs to the first `)`.

```pycon
>>> print(to_html("[the *docs*](https://example.com/docs) and [a file](notes/a.md)"), end="")
<p><a href="https://example.com/docs">the <em>docs</em></a> and <a href="notes/a.md">a file</a></p>

```

**Backslash escapes**: a backslash before `\`, `*`, `` ` ``, `[` or `]` prints that
character as is; before any other character the backslash stays.

```pycon
>>> print(to_html(r"\*not em\* \[not a link\] \_kept"), end="")
<p>*not em* [not a link] \_kept</p>

```

An unmatched marker is printed as is: `to_html` never raises for a `str` (it raises
`TypeError` for anything else).

```pycon
>>> print(to_html("**open, `tick, [bracket]"), end="")
<p>**open, `tick, [bracket]</p>

```

## Escaping and links

`&`, `<`, `>` and `"` are escaped everywhere, inside code too, so raw HTML shows as text.

```pycon
>>> print(to_html('<b>"bold"</b> & `<i>`'), end="")
<p>&lt;b&gt;&quot;bold&quot;&lt;/b&gt; &amp; <code>&lt;i&gt;</code></p>

```

A link keeps its URL when it is relative (no `:`) or its scheme is `http`, `https` or
`mailto`. The scheme is the text before the first `:`, compared case-insensitively after
removing whitespace and control characters; any other scheme becomes `#`. A relative URL
with a `:` in it is dropped too: write the colon as `%3A`.

```pycon
>>> print(to_html("[a](JaVaScRiPt:alert) [b](mailto:me@example.com) [c](/t?at=10:30)"), end="")
<p><a href="#">a</a> <a href="mailto:me@example.com">b</a> <a href="#">c</a></p>

```

## Not supported

Nested lists, blocks inside quotes, setext headings, indented code, `~~~` fences, `_em_`,
reference links, autolinks, images, tables, hard line breaks, HTML entities and raw HTML.
They are printed as text (escaped). ADR 0007 explains why.

## Command line

`python3 -m textkit markdown <file>` writes the HTML of a UTF-8 file to standard output:
exit 0, or exit 2 with `python3 -m textkit markdown: error: <path>: <reason>` on standard
error when the file is missing, unreadable or not valid UTF-8.
