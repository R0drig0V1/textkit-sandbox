<!-- Reference of the template engine textkit.template (plan task T3.4): syntax, filters, errors.
     Keep it in sync with textkit/template/ and with ADR 0008 (missing names). -->
# Templates: `textkit.template`

`render(template: str, context: dict[str, Any]) -> str` fills a template with values from a
dict. It is a small engine for plain text: names, filters, `if`, `for` and comments, nothing
more (no literals, operators, macros, includes or whitespace control). Short examples are in
the [usage guide](usage.md#templates-textkittemplate); the rule for names missing from the
context is [ADR 0008](decisions/0008-template-missing-names.md).

```python
from textkit.template import render, TemplateError, TemplateSyntaxError

render("Hi {{ user.name | upper }}!", {"user": {"name": "Ada"}})   # 'Hi ADA!'
```

From the shell: `python3 -m textkit render <template-file> <json-file>` (see
[Command line](#command-line)).

## How a template is read

The template is split into tags and text. A tag starts at `{{`, `{%` or `{#` and ends at the
first matching `}}`, `%}` or `#}` after it. Everything else is **text, copied exactly**: a
lone `{` or `}}`, `"\r\n"` and `"\r"` line endings, and HTML characters, which are never
escaped (the output is plain text). There is no whitespace control: the newline after a
`{% endif %}` stays in the output.

Spaces inside the delimiters are optional (`{{x}}` is `{{ x }}`, `{%if x%}` is
`{% if x %}`), and a tag may span lines.

The whole template is parsed before anything is rendered, so a syntax error is reported
whatever the context, even inside a branch that would not be rendered.

## Syntax

### Values: `{{ expr }}`

An expression is a **dotted name** followed by zero or more **filters**:

```
{{ title }}
{{ user.address.city }}
{{ title | slug | truncate:20 }}
```

- Each part of a dotted name is a Python identifier (`user`, `first_name`, `café`). The
  first part is looked up in the innermost `for` loop, then the enclosing loops, then the
  context; each following part is a **dict key** of the value so far (not an attribute or a
  list index: `items.0` is a syntax error).
- A value prints as `str(value)`, except **`None`, which prints as `""`**. So `True` prints
  `True`, `1.5` prints `1.5`, a list prints as Python shows it. A value is never rendered
  again: a context value `"{{ y }}"` prints as is.
- Filters apply from left to right to that printed text.

### Conditions: `{% if expr %} ... {% else %} ... {% endif %}`

The body renders when the expression is true by Python's `bool`: `0`, `0.0`, `""`, `[]`,
`{}`, `None` and `False` are false. With filters, the test is on the filtered text, so
`{% if flag | lower %}` is true for `False` (`"false"` is not empty). `else` is optional;
there is no `elif` (nest an `if` in the `else` instead).

A name missing from the context is **false** here, not an error (ADR 0008).

### Loops: `{% for item in expr %} ... {% endfor %}`

The expression must be a `list` (a JSON array); the body renders once per item with `item`
bound to it. Inside the body:

- `loop.index` is the position of the item, from 1;
- `loop` is always the innermost loop, and it hides a context key named `loop`; a loop
  variable cannot be named `loop`;
- the loop variable hides a context key or outer loop variable of the same name, until
  `endfor`.

### Comments: `{# ... #}`

A comment prints nothing; it ends at the first `#}`, and tags inside it are ignored.

Blocks nest freely, to any depth: an `if` inside a `for` inside an `if`. The parser and
the renderer both keep their own stack instead of nesting Python calls, so deep nesting
never hits Python's recursion limit.

## Filters

A fixed table over existing textkit functions; nothing else can be called.

| Filter | Function | Example: input -> output |
|--------|----------|--------------------------|
| `slug` | `textkit.strings.slugify` | `"Hello, World!"` -> `"hello-world"` |
| `snake` | `textkit.cases.to_snake_case` | `"userId"` -> `"user_id"` |
| `camel` | `textkit.cases.to_camel_case` | `"user_id"` -> `"userId"` |
| `kebab` | `textkit.cases.to_kebab_case` | `"userId"` -> `"user-id"` |
| `squeeze` | `textkit.strings.squeeze` | `"  a \n b "` -> `"a b"` |
| `strip_accents` | `textkit.strings.strip_accents` | `"Ñandú"` -> `"Nandu"` |
| `truncate:<width>` | `textkit.strings.truncate(text, width)` | `truncate:8`: `"Hello, World!"` -> `"Hello..."` |
| `upper` | `str.upper` | `"Ada"` -> `"ADA"` |
| `lower` | `str.lower` | `"Ada"` -> `"ada"` |

`truncate` needs an integer width of at least 3 (the length of its `"..."` suffix), written
with ASCII digits and an optional sign: `truncate:20`, `truncate : 20`. The other filters
take no argument. Both are checked while parsing.

## Errors

Two classes, importable from `textkit.template` (they are not in its `__all__`, which lists
functions only). `TemplateError` subclasses `textkit.errors.InvalidValueError`, so
`except TextkitError` catches both; neither is a `ValueError` (ADR 0006).

- `TemplateError`: rendering failed. Attributes `message`, `line` and `column`;
  `str(error)` is `"<line>:<column>: <message>"`.
- `TemplateSyntaxError(TemplateError)`: the template is not valid; raised by parsing,
  before any output.

**Positions** count from 1, columns in code points. A line ends after each `"\n"` only, so
a `"\r"` is one more column (`"a\r{{ b }}"`: the tag is at 1:3; `"a\r\n{{ b }}"`: at 2:1).
The position is that of the opening delimiter (`{{`, `{%`, `{#`) of the tag at fault; for a
block with no end tag, that of its opening tag.

### `TemplateSyntaxError`

| Cause | Example | Position |
|-------|---------|----------|
| Unterminated tag | `"{{ x"`, `"{% if x"`, `"{# note"` | the opening delimiter |
| Malformed name | `"{{ }}"`, `"{{ a..b }}"`, `"{{ items.0 }}"`, `"{{ a b }}"` | the tag |
| Unknown filter, or an empty one | `"{{ x \| title }}"`, `"{{ x \| }}"` | the tag |
| Bad filter argument | `"{{ x \| truncate }}"`, `truncate:x`, `truncate:2`, `"{{ x \| upper:2 }}"` | the tag |
| Empty or unknown block tag | `"{% %}"`, `"{% include x %}"`, `"{% elif x %}"` | the tag |
| `if` with no expression | `"{% if %}"` | the tag |
| Malformed `for` | `"{% for x %}"`, `"{% for a.b in xs %}"`, `"{% for loop in xs %}"` | the tag |
| An argument after `else`, `endif` or `endfor` | `"{% endif x %}"` | the tag |
| `else`, `endif` or `endfor` without its opening tag | `"{% endif %}"`, `"{% for x in xs %}{% else %}"` | the closing tag |
| A closing tag that does not match the innermost open block | `"{% if a %}{% endfor %}"` | the closing tag |
| A second `else` | `"{% if a %}{% else %}{% else %}..."` | the second `else` |
| A block with no end tag | `"{% if a %}text"` | the opening tag (the innermost unclosed one) |

### `TemplateError` (while rendering)

| Cause | Example | Position |
|-------|---------|----------|
| A name missing from the context in `{{ }}` (ADR 0008) | `render("{{ x }}", {})` | the `{{` |
| A name missing from the context in `for` (ADR 0008) | `render("{% for i in xs %}{% endfor %}", {})` | the `{%` of the `for` |
| A `for` over a value that is not a `list` (tuples, dicts, strings, `None`, or any expression with filters) | `{"xs": "ab"}` | the `{%` of the `for` |
| A dotted name through a value that is not a `dict`, in any tag | `"{{ user.name }}"` with `{"user": "Ada"}` | the tag |
| A value nested too deeply for `str` to print (a list or dict thousands of levels deep) | `{{ v }}` | the tag |

A missing name in `if` is not an error (it is false). `render` raises `TypeError` when the
template is not a `str` or the context not a `dict`.

## Command line

```sh
python3 -m textkit render page.txt values.json > out.txt
```

The template file and the JSON file are read as UTF-8 with no newline translation, so a
`"\r\n"` in the template stays `"\r\n"` in the output, and the result is written to stdout
as is (nothing at all for an empty result). The JSON file must hold an object, which
becomes the context.

| Exit | When | stderr |
|------|------|--------|
| 0 | rendered | nothing |
| 1 | a `TemplateError` or `TemplateSyntaxError` | `line:column: message` |
| 2 | a file is missing, unreadable or not UTF-8; the JSON is invalid, not an object, or holds a lone surrogate (`"\ud800"`: valid JSON, but no UTF-8 text); wrong arguments | `python3 -m textkit render: error: <path>: <reason>` (argparse usage for wrong arguments) |
| 2 | stdout's encoding cannot encode the result (for example under `PYTHONIOENCODING=ascii`); nothing is written | `python3 -m textkit render: error: stdout: cannot encode '<char>' as <encoding>` |
