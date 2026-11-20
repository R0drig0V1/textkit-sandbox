<!-- ADR 0008: the Markdown subset of textkit.markdown.to_html (plan task T3.5). -->
# 0008. The Markdown subset of `to_html`: what it leaves out, raw HTML and link schemes

## Context

`textkit.markdown.to_html(text) -> str` (plan task T3.5) converts Markdown to HTML. Full
CommonMark is a long specification (about 650 examples) with nested containers, lazy
continuation lines, reference links, entities and raw HTML; implementing it is out of
proportion for a standard-library helper package. The plan fixes a small subset and its
exact output instead. Three things need a recorded decision, because future readers will
ask why: what the subset leaves out (and so prints as plain text), why raw HTML is escaped
rather than passed through as Markdown allows, and why some link schemes are dropped.

The output is meant to be safe to put in a web page when the Markdown comes from someone
else: comments, issue bodies, user profiles.

## Decision

### The subset

Lines end at `"\n"`, `"\r\n"` or a lone `"\r"`; the ending is dropped before parsing (code
lines included), every output line ends in `"\n"` and `""` gives `""`. A blank line is
empty or holds only spaces and tabs. Every block marker must start at the first column.

- **Blocks:** ATX headings (`#` to `######` and a space); paragraphs (lines stripped of
  spaces and tabs, joined by one space); one-level lists, unordered (`-` or `*` and a space)
  or ordered (ASCII digits, `.` and a space; numbers not checked, no `start` attribute),
  where an item is its line plus the following lines indented by two spaces or more; fenced
  code blocks (three backticks and an optional language, its first word; an unclosed fence
  runs to the end); block quotes (`>` lines, holding paragraphs only; a `>` line with
  nothing after it separates two paragraphs); `---` alone on a line, a rule. A heading, a
  list item, a fence, a quote and `---` interrupt a paragraph; a blank line ends a list or
  a quote; an item of the other list kind starts a new list.
- **Inlines:** `**strong**`, `*em*`, code spans (a run of N backticks to the next run of
  exactly N; content as is), `[text](url)` (the URL runs to the first `)`), and a
  backslash before `\`, `*`, `` ` ``, `[` or `]` to print it as is (not in code spans,
  where a backslash is a character). `*` pairs by a simplified CommonMark delimiter rule
  (a run opens when no whitespace follows it, closes when none precedes it; closers pair
  with the nearest opener; strong when both runs have two left). Unmatched markers are
  printed as they are.

### What it leaves out

Everything else is text, printed (escaped) as written: setext headings (`---` under a line
is a rule, so `text\n---` is a paragraph and a rule), closing `#` sequences, indented code
blocks, `~~~` fences, nested lists and blocks inside items or quotes (`> # x` is a quoted
paragraph `# x`), lazy continuation lines, loose and tight lists, `+` bullets and `1)`
markers, `_` emphasis, hard line breaks, autolinks, reference links, images, link titles,
`(` `)` inside URLs, tables, HTML blocks, inline HTML and entities (`&copy;` prints as
`&amp;copy;`), and up to three spaces of indentation before a block marker. Each of these
either needs nested parsing that the one-level output shapes cannot express or adds rules
without adding much for short texts; leaving one out never loses text, only formatting.

### Raw HTML is escaped

Markdown passes raw HTML through. `to_html` never does: `&`, `<`, `>` and `"` are escaped in
text, in code spans and blocks, in the code language and in link URLs, so `<script>` is
printed, not run. A sanitizer that lets "safe" tags through needs an HTML parser and an
allowlist of tags and attributes, and its bugs are cross-site scripting holes; escaping
everything has no such bugs and the subset already covers the formatting a short text needs.
`'` is not escaped: no attribute is single-quoted.

### Unsafe link schemes become `#`

Escaping does not make a link safe: `[x](javascript:alert(1))` is valid HTML that runs code
when clicked, and so is a `data:` URL. A link URL whose scheme is not `http`, `https` or
`mailto` is replaced by `#` (the text stays, so nothing is lost). The scheme is the text
before the first `:`, with every whitespace and control character removed, compared
case-insensitively: browsers drop tabs and newlines inside a URL and control characters and
spaces at its start, so `java\tscript:` and `JaVaScRiPt:` run as `javascript:`; removing
every such character is a superset of what browsers remove, so it can flag more URLs but
never fewer. An allowlist, not a blocklist: a scheme nobody thought of (`vbscript:`,
whatever comes next) is dropped by default.

A URL **with no scheme** is relative and kept. That is the case when it has no `:` or when
the text before its first `:` (after the removal) is not a scheme name as RFC 3986 and
browsers read it (an ASCII letter, then letters, digits, `+`, `-` or `.`): browsers treat
such a URL as relative too, so `/wiki/Help:Contents` and `page?q=a:b` keep working.

## Consequences

- The output is safe to embed in a page as it is: no tag, attribute or script can come
  from the input, at the price of no raw HTML at all.
- Valid CommonMark that uses a left-out construct renders differently (as text) than on
  GitHub; docs/markdown.md lists the subset with an example of each construct.
- Inline parsing does not backtrack and takes time linear in the length of the text (up
  to a logarithmic factor for index lookups), hostile input included (hundreds of
  thousands of unmatched or overlapping markers): backtick runs and `)` are indexed once,
  the emphasis pass pairs with a stack of open delimiters instead of rewriting a list, and
  text is joined once. Rendering is iterative, so deep nesting cannot reach Python's
  recursion limit. `tests/test_markdown.py` checks that four times the input takes well
  under sixteen times the time.
- Overlapping markers nest by the nearest-opener rule, not by CommonMark's:
  `**a *b** c*` gives `<em><em>a <em>b</em></em> c</em>`. The HTML is well formed; only
  the choice of tags can differ from other renderers.
- The tests (`tests/test_markdown.py`) find this ADR by its slug, parse the table below with
  `ast.literal_eval` and check that their case list equals it and that `to_html` gives every
  output, so the table and the code cannot drift apart. Changing a row means amending this
  ADR.

## Cases

Each cell is a Python string literal; a backtick in it is written `\x60` and a `|` would be
written `\x7c`, so that the table renders and parses.

| Input | Output |
|-------|--------|
| `''` | `''` |
| `'# Title'` | `'<h1>Title</h1>\n'` |
| `'###### Six'` | `'<h6>Six</h6>\n'` |
| `'####### Seven'` | `'<p>####### Seven</p>\n'` |
| `'#NoSpace'` | `'<p>#NoSpace</p>\n'` |
| `'one\ntwo'` | `'<p>one two</p>\n'` |
| `'one\n\ntwo'` | `'<p>one</p>\n<p>two</p>\n'` |
| `'- a\n- b'` | `'<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n'` |
| `'* a\n  more\n* b'` | `'<ul>\n<li>a more</li>\n<li>b</li>\n</ul>\n'` |
| `'1. a\n7. b'` | `'<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n'` |
| `'- a\n\n- b'` | `'<ul>\n<li>a</li>\n</ul>\n<ul>\n<li>b</li>\n</ul>\n'` |
| `'- a\n1. b'` | `'<ul>\n<li>a</li>\n</ul>\n<ol>\n<li>b</li>\n</ol>\n'` |
| `'\x60\x60\x60\n<x>\n\x60\x60\x60'` | `'<pre><code>&lt;x&gt;\n</code></pre>\n'` |
| `'\x60\x60\x60python\nprint(1)\n\x60\x60\x60'` | `'<pre><code class="language-python">print(1)\n</code></pre>\n'` |
| `'\x60\x60\x60a"b\nx\n\x60\x60\x60'` | `'<pre><code class="language-a&quot;b">x\n</code></pre>\n'` |
| `'\x60\x60\x60\nno closing fence'` | `'<pre><code>no closing fence\n</code></pre>\n'` |
| `'> a\n> b\n>\n> c'` | `'<blockquote>\n<p>a b</p>\n<p>c</p>\n</blockquote>\n'` |
| `'> # not a heading'` | `'<blockquote>\n<p># not a heading</p>\n</blockquote>\n'` |
| `'> q\n\nafter'` | `'<blockquote>\n<p>q</p>\n</blockquote>\n<p>after</p>\n'` |
| `'---'` | `'<hr>\n'` |
| `'para\n# Heading'` | `'<p>para</p>\n<h1>Heading</h1>\n'` |
| `'para\n- item'` | `'<p>para</p>\n<ul>\n<li>item</li>\n</ul>\n'` |
| `'para\n\x60\x60\x60\ncode\n\x60\x60\x60'` | `'<p>para</p>\n<pre><code>code\n</code></pre>\n'` |
| `'para\n> quote'` | `'<p>para</p>\n<blockquote>\n<p>quote</p>\n</blockquote>\n'` |
| `'para\n---'` | `'<p>para</p>\n<hr>\n'` |
| `'# Title\r\n'` | `'<h1>Title</h1>\n'` |
| `'\x60\x60\x60py\r\nx = 1\r\n\x60\x60\x60\r\n'` | `'<pre><code class="language-py">x = 1\n</code></pre>\n'` |
| `'a\rb'` | `'<p>a b</p>\n'` |
| `'**strong**'` | `'<p><strong>strong</strong></p>\n'` |
| `'*em*'` | `'<p><em>em</em></p>\n'` |
| `'\x60code\x60'` | `'<p><code>code</code></p>\n'` |
| `'[text](https://example.com)'` | `'<p><a href="https://example.com">text</a></p>\n'` |
| `'*a **b** c*'` | `'<p><em>a <strong>b</strong> c</em></p>\n'` |
| `'**unclosed'` | `'<p>**unclosed</p>\n'` |
| `'a * b'` | `'<p>a * b</p>\n'` |
| `'\x60unclosed'` | `'<p>\x60unclosed</p>\n'` |
| `'[no url]'` | `'<p>[no url]</p>\n'` |
| `'\\* \\\x60 \\[ \\] \\\\'` | `'<p>* \x60 [ ] \\</p>\n'` |
| `'\\a'` | `'<p>\\a</p>\n'` |
| `'\x60\\*\x60'` | `'<p><code>\\*</code></p>\n'` |
| `'<b>&"</b>'` | `'<p>&lt;b&gt;&amp;&quot;&lt;/b&gt;</p>\n'` |
| `'\x60<b>&"</b>\x60'` | `'<p><code>&lt;b&gt;&amp;&quot;&lt;/b&gt;</code></p>\n'` |
| `'[a](https://x.test/?a=1&b="2")'` | `'<p><a href="https://x.test/?a=1&amp;b=&quot;2&quot;">a</a></p>\n'` |
| `'[x](javascript:alert(1))'` | `'<p><a href="#">x</a>)</p>\n'` |
| `'[x](JaVaScRiPt:alert(1))'` | `'<p><a href="#">x</a>)</p>\n'` |
| `'[x](java\tscript:alert(1))'` | `'<p><a href="#">x</a>)</p>\n'` |
| `'[x](data:text/html,hi)'` | `'<p><a href="#">x</a></p>\n'` |
| `'[x](mailto:a@b.test)'` | `'<p><a href="mailto:a@b.test">x</a></p>\n'` |
| `'[x](HTTP://example.com)'` | `'<p><a href="HTTP://example.com">x</a></p>\n'` |
| `'[x](/wiki/Help:Contents)'` | `'<p><a href="/wiki/Help:Contents">x</a></p>\n'` |
| `'[x](page.html)'` | `'<p><a href="page.html">x</a></p>\n'` |
