<!-- ADR 0007: the Markdown subset of textkit.markdown.to_html, its escaping and its link
     schemes (plan task T3.5). The case table at the end is parsed by tests/test_markdown.py. -->
# 0007. Markdown to HTML: the subset, escaping everything, and dropping link schemes

## Context

`textkit.markdown.to_html(text) -> str` (plan task T3.5) turns Markdown into HTML with the
standard library only. Full CommonMark is a long specification (nested containers, lazy
continuation, reference links, setext headings, about 650 example cases); implementing it
is out of proportion for a package of small helpers, and an implementation that tries and
gets it half right is worse than a stated subset.

The output is meant to be put into a web page. Markdown allows raw HTML and any link URL,
so a converter that passes them through turns every Markdown input into a script
injection: `<script>` in the text, `<img onerror=...>`, or `[click](javascript:...)`.
Callers of a text helper do not expect to sanitize its output.

## Decision

**The subset.** Blocks: ATX headings (`#` to `######` and a space), paragraphs, one-level
unordered (`-`, `*`) and ordered (`1.`) lists, fenced code blocks (three backticks, an
optional language), block quotes holding paragraphs, and a `---` rule. Inlines:
`**strong**`, `*em*`, `` `code` ``, `[text](url)` and backslash escapes of `\`, `*`,
`` ` ``, `[` and `]`. The exact rules are in the module docstrings of
`textkit/markdown/blocks.py` and `inlines.py`, and in [docs/markdown.md](../markdown.md).

**Left out**, on purpose:

- nested lists and nested blocks in quotes: an indented `- x` continues the item above it,
  and the text after `>` is always paragraph text;
- setext headings (`Title` over `===`), closing `#`s on a heading, indented code blocks,
  `~~~` fences, `***` and `___` rules, `_em_` and `__strong__`, multi-backtick code spans;
- reference links, autolinks (`<https://...>`), images, tables, footnotes, hard line breaks;
- lazy continuation: a line that is not indented and is not another item ends a list, and
  a line without `>` ends a quote;
- HTML entities (`&copy;`) and raw HTML, which are text (see below).

Anything outside the subset is printed as text, escaped, so the output is always valid and
safe; it may just show the Markdown characters. Block markers count only at the start of a
line; "blank" means spaces and tabs only.

**Line endings.** A line ends at `"\n"`, `"\r\n"` or a lone `"\r"`, and the ending is
dropped before parsing, code block lines included. Every output line ends in `"\n"`, so the
result does not depend on the platform the Markdown was written on.

**Escaping everything.** Raw HTML is never passed through: `&`, `<`, `>` and `"` are
escaped in all text, in code spans and code blocks, in the language of a fence (it becomes
an attribute) and in link URLs. `'` is not escaped: every attribute textkit writes is
double-quoted. This makes the output safe to embed whatever the input, at the cost of not
supporting inline HTML at all (a `<br>` in the source shows as `<br>`). An allowlist of
"safe" tags was rejected: it is a sanitizer, with its own long history of bypasses
(attributes, encodings, malformed nesting), and out of scope for a text helper.

**Link schemes.** A link URL keeps its value only when it is relative (it has no `:`) or
its scheme is `http`, `https` or `mailto`. The scheme is the text before the first `:`,
compared case-insensitively after removing whitespace and control characters, because
browsers ignore those (`java\tscript:` and `\x01javascript:` run script just like
`javascript:`). Any other scheme (`javascript:`, `vbscript:`, `data:`, `file:`, schemes
not yet invented) is replaced by `#`. An allowlist was chosen over a blocklist of known
bad schemes because a blocklist fails open on the first scheme it forgets.

## Consequences

- The output is safe to insert into a page with no further sanitizing, as long as it is
  inserted as HTML content (not inside a `<script>` or a style).
- Documents that rely on CommonMark features outside the subset render differently from
  GitHub or other renderers; docs/markdown.md lists the subset so a reader can check.
- A relative URL that contains a `:` (`/a?t=10:30`) is treated as having a scheme and
  becomes `#`; write the colon as `%3A`. A URL ends at its first `)`, so a URL with
  parentheses must encode them (`%28`, `%29`).
- Links to schemes such as `tel:` or `ftp:` are dropped; adding one is a change to
  `ALLOWED_SCHEMES` in `textkit/markdown/html.py`, this ADR and its table.
- Markers are matched by scanning forward from each opener, which takes time quadratic in
  the length of a block full of unmatched `*` or `[`; it is meant for documents of a few
  hundred kilobytes at most.
- `tests/test_markdown.py` converts every row below and checks that its own case list
  equals this table (parsed with `ast.literal_eval`), so the table and the tests cannot
  drift apart.

## Cases

Inputs and outputs are Python string literals (`ast.literal_eval`); a backtick is written
`\x60` and a `|` would be written `\x7c`, so that each cell stays one code span of the
table.

| Input | Output |
|-------|--------|
| `""` | `""` |
| `"# Title"` | `"<h1>Title</h1>\n"` |
| `"###### Six"` | `"<h6>Six</h6>\n"` |
| `"####### Seven"` | `"<p>####### Seven</p>\n"` |
| `"#NoSpace"` | `"<p>#NoSpace</p>\n"` |
| `"one\ntwo\n\nthree"` | `"<p>one two</p>\n<p>three</p>\n"` |
| `"- a\n- b"` | `"<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n"` |
| `"* a\n  more\n- b"` | `"<ul>\n<li>a more</li>\n<li>b</li>\n</ul>\n"` |
| `"1. a\n7. b"` | `"<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n"` |
| `"- a\nnext"` | `"<ul>\n<li>a</li>\n</ul>\n<p>next</p>\n"` |
| `"\x60\x60\x60\nx\n\x60\x60\x60"` | `"<pre><code>x\n</code></pre>\n"` |
| `"\x60\x60\x60python\nprint(1)\n\n\x60\x60\x60"` | `"<pre><code class=\"language-python\">print(1)\n\n</code></pre>\n"` |
| `"\x60\x60\x60\nunclosed"` | `"<pre><code>unclosed\n</code></pre>\n"` |
| `"> a\n> b\n>\n> c"` | `"<blockquote>\n<p>a b</p>\n<p>c</p>\n</blockquote>\n"` |
| `"> # not a heading\n> - not an item"` | `"<blockquote>\n<p># not a heading - not an item</p>\n</blockquote>\n"` |
| `"---"` | `"<hr>\n"` |
| `"text\n# Heading"` | `"<p>text</p>\n<h1>Heading</h1>\n"` |
| `"text\n- item"` | `"<p>text</p>\n<ul>\n<li>item</li>\n</ul>\n"` |
| `"text\n\x60\x60\x60\ncode\n\x60\x60\x60"` | `"<p>text</p>\n<pre><code>code\n</code></pre>\n"` |
| `"text\n> quote"` | `"<p>text</p>\n<blockquote>\n<p>quote</p>\n</blockquote>\n"` |
| `"text\n---"` | `"<p>text</p>\n<hr>\n"` |
| `"**strong**"` | `"<p><strong>strong</strong></p>\n"` |
| `"*em*"` | `"<p><em>em</em></p>\n"` |
| `"**a *b* c**"` | `"<p><strong>a <em>b</em> c</strong></p>\n"` |
| `"\x60code\x60"` | `"<p><code>code</code></p>\n"` |
| `"[text](https://example.com)"` | `"<p><a href=\"https://example.com\">text</a></p>\n"` |
| `"[mail](mailto:a@example.com)"` | `"<p><a href=\"mailto:a@example.com\">mail</a></p>\n"` |
| `"[rel](docs/a.md)"` | `"<p><a href=\"docs/a.md\">rel</a></p>\n"` |
| `"[js](javascript:alert)"` | `"<p><a href=\"#\">js</a></p>\n"` |
| `"[js](JaVaScRiPt:alert)"` | `"<p><a href=\"#\">js</a></p>\n"` |
| `"[js](java\tscript:alert)"` | `"<p><a href=\"#\">js</a></p>\n"` |
| `"[data](data:text/html,x)"` | `"<p><a href=\"#\">data</a></p>\n"` |
| `"[up](HTTPS://example.com)"` | `"<p><a href=\"HTTPS://example.com\">up</a></p>\n"` |
| `"[js](\x01javascript:alert)"` | `"<p><a href=\"#\">js</a></p>\n"` |
| `"[t](/a?t=10:30)"` | `"<p><a href=\"#\">t</a></p>\n"` |
| `"\\*a\\* \\\x60 \\[b\\] \\\\"` | `"<p>*a* \x60 [b] \\</p>\n"` |
| `"\\_ \\#"` | `"<p>\\_ \\#</p>\n"` |
| `"\x60a\\*b\x60"` | `"<p><code>a\\*b</code></p>\n"` |
| `"**a"` | `"<p>**a</p>\n"` |
| `"*a"` | `"<p>*a</p>\n"` |
| `"2 * 3 * 4"` | `"<p>2 * 3 * 4</p>\n"` |
| `"\x60a"` | `"<p>\x60a</p>\n"` |
| `"[a]"` | `"<p>[a]</p>\n"` |
| `"<b>&\"x\"'</b>"` | `"<p>&lt;b&gt;&amp;&quot;x&quot;'&lt;/b&gt;</p>\n"` |
| `"\x60<a href=\"x\">\x60"` | `"<p><code>&lt;a href=&quot;x&quot;&gt;</code></p>\n"` |
| `"\x60\x60\x60\n<script>&\n\x60\x60\x60"` | `"<pre><code>&lt;script&gt;&amp;\n</code></pre>\n"` |
| `"\x60\x60\x60a\"b\nx\n\x60\x60\x60"` | `"<pre><code class=\"language-a&quot;b\">x\n</code></pre>\n"` |
| `"[a](\"><script>)"` | `"<p><a href=\"&quot;&gt;&lt;script&gt;\">a</a></p>\n"` |
| `"# Title\r\n"` | `"<h1>Title</h1>\n"` |
| `"\x60\x60\x60py\r\nx = 1\r\n\x60\x60\x60\r\n"` | `"<pre><code class=\"language-py\">x = 1\n</code></pre>\n"` |
| `"a\rb"` | `"<p>a b</p>\n"` |
