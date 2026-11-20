<!-- The Markdown subset of textkit.markdown.to_html (plan task T3.5): every block and inline,
with an example of each. The decisions behind it (what is left out, raw HTML, link schemes)
are in docs/decisions/0008-markdown-subset-raw-html-and-link-schemes.md, whose case table
the tests check. -->
# Markdown: `textkit.markdown`

`to_html(text)` converts a small subset of Markdown to HTML. It is meant for short texts that
may come from anyone (comments, descriptions): its output never contains HTML from the
input, and links can only point to `http`, `https` and `mailto` URLs or to relative ones.

```python
from textkit.markdown import to_html
```

From the shell, `python3 -m textkit markdown <file>` writes `to_html` of a UTF-8 file to
stdout (exit 0), or exits 2 with `python3 -m textkit markdown: error: <file>: <reason>` when
the file is missing, unreadable or not valid UTF-8.

## Lines and output

- A line ends at `\n`, `\r\n` or a lone `\r`; the ending is dropped before parsing, so the
  three give the same HTML. Other separators (`\f`, `\x85`, ` `) are text.
- A *blank* line is empty or holds only spaces and tabs.
- Every block marker (`#`, `-`, `*`, `1.`, `>`, three backticks, `---`) must be at the start
  of the line. An indented marker is text (or, under a list item, part of the item).
- Every output line ends in `\n`; no other whitespace is added. `""` gives `""`.

The package has three modules: `blocks.py` (lines to blocks), `inlines.py` (the text of a
block to inline nodes) and `html.py` (escaping, link checks, the layout, `to_html`).

## Blocks

Each example shows the input, then the output.

### Headings

`#` to `######`, then a space. The text is stripped of surrounding spaces and tabs. Seven
`#`, or no space, make a paragraph.

```text
## Install
```

```html
<h2>Install</h2>
```

### Paragraphs

Consecutive non-blank lines, each stripped of surrounding spaces and tabs, joined by one
space. A blank line ends a paragraph, and so does a line that starts a heading, a list item,
a fence, a quote or a rule.

```text
First line
  second line

Next paragraph
```

```html
<p>First line second line</p>
<p>Next paragraph</p>
```

### Lists

`-` or `*` and a space make an unordered list; digits, `.` and a space an ordered one (the
numbers are not checked and no `start` attribute is written). An item is its line plus the
following lines indented by two spaces or more, joined by one space. Lists have one level:
an indented `- x` belongs to the item above it. A blank line, an item of the other kind or
any other line ends the list.

```text
- apples
- pears that are
  very ripe
```

```html
<ul>
<li>apples</li>
<li>pears that are very ripe</li>
</ul>
```

```text
3. three
1. one
```

```html
<ol>
<li>three</li>
<li>one</li>
</ol>
```

### Fenced code blocks

Three backticks, then an optional language (its first word is used). The lines up to a line
of three backticks (trailing spaces allowed) are written exactly as they are, escaped; an
unclosed fence runs to the end of the text. A line with a fourth backtick (four backticks in
a row, or a backtick in the language) is not a fence: it is text.

````text
```python
if a < b:
    print("*a*")
```
````

```html
<pre><code class="language-python">if a &lt; b:
    print(&quot;*a*&quot;)
</code></pre>
```

Without a language the opening tag is `<pre><code>`.

### Block quotes

Lines that start with `>`. The text after `>` is always paragraph text, never another block
(`> # x` is a paragraph `# x`); a `>` line with nothing after it separates two paragraphs. A
blank line, or any line that does not start with `>`, ends the quote.

```text
> Quoted *text*
> on two lines
>
> # not a heading
```

```html
<blockquote>
<p>Quoted <em>text</em> on two lines</p>
<p># not a heading</p>
</blockquote>
```

### Horizontal rules

`---` alone on a line (trailing spaces allowed). Under a paragraph it is a rule too, not a
heading underline.

```text
above
---
```

```html
<p>above</p>
<hr>
```

## Inlines

Inline syntax works in headings, paragraphs, list items and quoted paragraphs; never in code
blocks. A marker that is not matched is printed as it is.

| Input | Output |
|-------|--------|
| `**strong**` | `<strong>strong</strong>` |
| `*em*` | `<em>em</em>` |
| `*a **b** c*` | `<em>a <strong>b</strong> c</em>` |
| `` `x < 1` `` | `<code>x &lt; 1</code>` |
| ``` `` a`b `` ``` | ``` <code> a`b </code> ``` |
| `[docs](https://example.com)` | `<a href="https://example.com">docs</a>` |
| `\*not em\*` | `*not em*` |
| `a * b`, `**open` | `a * b`, `**open` |

- **Strong and emphasis.** A run of `*` can open when no whitespace follows it and close when
  none precedes it. Each closer pairs with the nearest opener before it: strong when both
  have two `*` left, emphasis otherwise, so `***a***` is `<em><strong>a</strong></em>` and
  `**a*` is `*<em>a</em>`. Overlapping markers nest by the same rule, so
  `**a *b** c*` is `<em><em>a <em>b</em></em> c</em>` (CommonMark differs). `_` is not a
  marker.
- **Code spans.** A run of backticks opens a span that closes at the next run of the same
  length; the content is kept as it is (no trimming) and escaped. A backslash in a code span
  is a backslash.
- **Links.** `[text](url)`: the text may hold other inlines but no unescaped `[`; the URL is
  everything up to the first `)`, stripped of spaces and tabs (so a `)` cannot be part of a
  URL: write `%29`). Emphasis never crosses the edge of a link.
- **Backslash escapes.** A backslash before `\`, `*`, `` ` ``, `[` or `]` prints that
  character as it is. Before any other character, or at the end, the backslash stays.

## Safety

- **Raw HTML is escaped.** `&`, `<`, `>` and `"` become `&amp;`, `&lt;`, `&gt;` and
  `&quot;` everywhere: text, code, the code language and link URLs. `<b>` prints as `<b>`
  on the page, and entities such as `&copy;` print as typed.
- **Link schemes.** The scheme is the text before the first `:`, with whitespace and control
  characters removed, compared case-insensitively. `http`, `https` and `mailto` are kept;
  any other scheme (`javascript`, `JaVaScRiPt`, `java<TAB>script`, `data`, `ftp`...) is
  replaced by `#`, keeping the link text. A URL with no scheme is relative and kept: no `:`
  at all, or text before the first `:` that is not a scheme name (an ASCII letter, then
  letters, digits, `+`, `-` or `.`), such as `/wiki/Help:Contents`.

```text
[ok](https://example.com) [bad](JaVaScRiPt:alert) <script>
```

```html
<p><a href="https://example.com">ok</a> <a href="#">bad</a> &lt;script&gt;</p>
```

## Left out

Everything else is printed as text: setext headings, closing `#` sequences, indented code
blocks, `~~~` fences, nested lists and blocks inside items or quotes, lazy continuation
lines, `+` bullets and `1)` markers, `_` emphasis, hard line breaks, autolinks, reference
links, images, link titles, tables, raw HTML and entities. The reasons are in ADR 0008.
