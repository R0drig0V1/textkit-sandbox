<!-- Reference of the template engine textkit.template (plan task T3.4): syntax, filters,
errors. Keep it in sync with textkit/template/ and with ADR 0006 (missing names). -->
# Templates: `textkit.template`

```python
from textkit.template import render, TemplateError, TemplateSyntaxError

render("Hello, {{ user.name | upper }}!", {"user": {"name": "Ada"}})  # 'Hello, ADA!'
```

`render(template: str, context: dict[str, Any]) -> str` fills a template with values from a
dict. It is meant for plain text (messages, file headers, generated config): the output is
never HTML-escaped. A short example of each feature is in [usage.md](usage.md#templates-textkittemplate);
the command line form is `python3 -m textkit render <template-file> <json-file>`.

## Syntax

| Tag | Meaning |
|-----|---------|
| `{{ expr }}` | Prints the value of `expr`. |
| `{% if expr %} ... {% else %} ... {% endif %}` | Renders the first part when `expr` is true (Python's `bool`), else the part after `else` (optional). |
| `{% for item in expr %} ... {% endfor %}` | Renders the body once per element of the list `expr`, with `item` bound to it and `loop.index` counting from 1. |
| `{# comment #}` | Prints nothing. A comment may contain tags; it ends at the first `#}`. |

- **Text** outside tags is copied as is: line endings (`"\r\n"` stays `"\r\n"`), spaces
  and a lone `{` or `}`. There is no whitespace control: the newline after a
  `{% endif %}` is printed like any other text.
- **Spaces inside the delimiters are optional**: `{{x}}` is `{{ x }}`, `{%if x%}` is
  `{% if x %}`. Tags may span lines.
- A tag ends at the first closing delimiter of its own kind (`}}`, `%}` or `#}`); there are
  no string literals, so a tag cannot contain its own closing delimiter.
- **Blocks nest**, up to 100 levels deep.
- **Expressions** are a dotted name with optional filters: `user.name | slug | truncate:20`.
  Each part of the name is a Python identifier (Unicode letters allowed, no digits first:
  `items.0` is a syntax error). A dot follows **dict keys only**: never attributes or list
  indexes. Spaces around `.` are not allowed; spaces around `|` and `:` are.
- **Names** are looked up in the innermost `for` first, then outwards, then in the context.
  Inside a `for`, `loop` is the innermost loop (`{"index": n}`) and hides a context key named
  `loop`; the loop variable hides a context key of the same name until `{% endfor %}`. `loop`
  cannot be a loop variable.

## Values

- A value prints as `str(value)`: `True` prints `True`, `2.5` prints `2.5`, a list prints as
  Python writes it. **`None` prints as `""`.** Filters apply to that string.
- In `if`, a value without filters is tested with `bool` (`0`, `""`, `[]`, `{}`, `None` and
  `False` are false; `"0"` is true). With filters, the filtered text is tested:
  `{% if flag | lower %}` is true for `False`, whose text is `"false"`.
- `for` accepts a `list` only: not a string, tuple, dict or `None`, and not a filtered value
  (filters always produce text).
- **Missing names** (ADR 0006, [decisions/0006](decisions/0006-template-missing-names.md)): a
  name that is not in the context, or a key missing from a dict on the way, is an error in
  `{{ }}` and `for` and is **false** in `if`, so `{% if user.admin %}` can test an optional
  key. The price: a typo inside an `if` is not reported, it is just false. A dotted name
  through a value that is not a dict (`user.name` with `user` a string or `None`) is an
  error everywhere, `if` included.

## Filters

A fixed table over textkit's own functions; templates cannot add filters. Each takes the
text and returns text.

| Filter | Function | Example |
|--------|----------|---------|
| `slug` | `textkit.strings.slugify` | `Hello, World!` -> `hello-world` |
| `snake` | `textkit.cases.to_snake_case` | `HTTPServer` -> `http_server` |
| `camel` | `textkit.cases.to_camel_case` | `user_id` -> `userId` |
| `kebab` | `textkit.cases.to_kebab_case` | `userId` -> `user-id` |
| `squeeze` | `textkit.strings.squeeze` | `" a   b "` -> `a b` |
| `strip_accents` | `textkit.strings.strip_accents` | `Ñandú` -> `Nandu` |
| `truncate:<width>` | `textkit.strings.truncate` | `truncate:8` on `Hello, World!` -> `Hello...` |
| `upper` | `str.upper` | `Ada` -> `ADA` |
| `lower` | `str.lower` | `Ada` -> `ada` |

`truncate` is the only filter with an argument: the width, in ASCII digits, at least 3 (the
length of its `...` suffix). It is checked when the template is parsed, not when it is
rendered.

## Errors

Both classes are importable from `textkit.template` and subclass `ValueError` (they will
subclass `textkit.errors.InvalidValueError` once that exists, plan task T3.2).

- **`TemplateError`** has `message`, `line` and `column`; `str(error)` is
  `"<line>:<column>: <message>"`. Both numbers count from 1. A line ends after each `"\n"`
  only, so a `"\r"` (alone or in `"\r\n"`) is a column; columns count code points.
  The position is that of the opening delimiter (`{{`, `{%` or `{#`) of the offending tag.
- **`TemplateSyntaxError(TemplateError)`** is raised while parsing, before anything is
  rendered; a template either renders completely or raises.

| Error | Class | Example | Position |
|-------|-------|---------|----------|
| unterminated `{{`, `{%` or `{#` | `TemplateSyntaxError` | `a {{ b` | the opener |
| a block with no end tag | `TemplateSyntaxError` | `{% if a %}yes` | the opening tag (the innermost one when several are open) |
| an unknown tag | `TemplateSyntaxError` | `{% include x %}`, `{% elif a %}` | the tag |
| an empty tag | `TemplateSyntaxError` | `{% %}` | the tag |
| an unknown filter | `TemplateSyntaxError` | `{{ a \| title }}` | the tag |
| a bad filter argument | `TemplateSyntaxError` | `truncate:x`, `truncate:2`, `truncate`, `upper:3` | the tag |
| `else`, `endif` or `endfor` without their opening tag | `TemplateSyntaxError` | `{% endif %}`, `{% if a %}{% endfor %}` | the closing tag |
| a second `else` in one `if` | `TemplateSyntaxError` | `{% if a %}{% else %}{% else %}` | the second `else` |
| an end tag with something after it | `TemplateSyntaxError` | `{% endif a %}` | the tag |
| a malformed expression | `TemplateSyntaxError` | `{{ }}`, `{{ a b }}`, `{{ a.0 }}`, `{{ a \| }}`, `{% if %}` | the tag |
| a malformed `for` | `TemplateSyntaxError` | `{% for x %}`, `{% for a.b in c %}`, `{% for loop in c %}` | the tag |
| blocks nested deeper than 100 | `TemplateSyntaxError` | | the 101st opening tag |
| a missing name in `{{ }}` or `for` | `TemplateError` | `{{ nmae }}` | the tag |
| a dotted name through a value that is not a dict | `TemplateError` | `{{ user.name }}` with `user = "Ada"` | the tag |
| a `for` over a value that is not a list | `TemplateError` | `{% for c in name %}` with `name = "abc"` | the `for` tag |

`render` raises `TypeError` when `template` is not a `str` or `context` is not a `dict`.

## Command line

```sh
python3 -m textkit render <template-file> <json-file>
```

Reads both files as UTF-8 with no newline translation, renders the template with the JSON
object as the context, and writes the result to stdout unchanged (no newline added). Exit
codes: 0 on success; 1 for any `TemplateError`, with `line:column: message` on stderr; 2 for
a file that cannot be read, is not valid UTF-8, or (the JSON file) is not valid JSON or not a
JSON object, with `python3 -m textkit render: error: <path>: <reason>` on stderr.

## How it works

Three stages, one module each, in `textkit/template/`:

1. `lexer.py` splits the template into text, output-tag and block-tag tokens, each with its
   line and column; comments are dropped here.
2. `parser.py` builds a tree (`Text`, `Output`, `If`, `For`) with an explicit stack of open
   blocks and raises every `TemplateSyntaxError`, filters included (`filters.py` holds the
   table).
3. `renderer.py` walks the tree with a stack of scopes (the context, then one per enclosing
   `for`) and raises the render-time `TemplateError`s.
