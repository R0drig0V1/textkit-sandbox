<!-- ADR 0008: names missing from the context in textkit.template.render (plan task T3.4). -->
# 0008. `textkit.template`: names missing from the context

## Context

`textkit.template.render(template, context)` (plan task T3.4) looks names up in a dict:
`{{ user.name }}` reads `context["user"]["name"]`. The plan leaves open what happens when a
name is not there, in output tags and in `{% if %}`, and asks this ADR to settle it together
with how `None`, booleans and numbers print and test. The options were:

1. **Empty text everywhere** (Jinja2's default `Undefined`, Django): a missing name prints
   `""` and is false. Templates never fail on data, but a typo (`{{ usre.name }}`) silently
   prints nothing, and the mistake shows up only when someone reads the output.
2. **An error everywhere** (Jinja2's `StrictUndefined`): every typo is caught at once, but
   an optional key cannot be tested: `{% if user.admin %}` fails for every user without an
   `admin` key, so the data must carry every key, `false` included.
3. **An error where the value is used, false where it is tested**: what this ADR takes.

The same choice decides two neighbours: a dotted name through a value that is not a dict
(`user.name` with `user` a string or `None`), and `None` itself, which JSON produces for
`null` and which `str` would print as `"None"`.

## Decision

1. **Output and `for`: a missing name is an error.** `{{ x }}` and `{% for i in x %}` raise
   `TemplateError` when `x` (or any segment of `x.y.z`) is not in the context, at the
   position of the tag's opening delimiter (`{{` or `{%`). Its message is
   `'<dotted name>' is not defined`. Filters do not change this: `{{ x | upper }}` fails
   the same way.
2. **`if`: a missing name is false.** `{% if user.admin %}` takes the `else` branch (or
   prints nothing) when `user` or its `admin` key is missing, with or without filters. This
   is the one place a template asks "is this here?", and the only way, since the syntax has
   no `defined` test.
3. **A dotted name through a value that is not a dict is an error, also in `if`.**
   `{{ user.name }}` and `{% if user.name %}` raise `TemplateError` when `user` is a string,
   a list, a number or `None`. Rule 2 covers *absent* keys only: a value of the wrong type is
   a mismatch between template and data, not an optional field. `.` follows dict keys only,
   never attributes or list indexes.
4. **`None` prints as `""`** and is false in `if` (`bool(None)`). With filters, the filters
   apply to `""`. `{% for %}` over `None` is an error: `None` is not a list.
5. **Everything else prints as `str(value)`**: `True` and `False` print as `"True"` and
   `"False"` (Python's spelling, not JSON's), numbers as Python writes them (`2.5`, `-12`).
   In `if`, a value without filters is tested with Python's `bool`: `0`, `0.0`, `""`, `[]`
   and `{}` are false, `"0"` is true. **With filters, the filtered text is tested**, because
   a filter always produces text: `{% if x | lower %}` with `x = False` tests `"false"`,
   which is true.

Inside a `for`, the loop variable and `loop` are looked up first (innermost loop first), so
the same rules apply to `{{ item.key }}` and `{{ loop.index }}`: `{{ loop.size }}` is a
missing name.

## Consequences

- A typo in an output tag fails loudly with its line and column, which the `render`
  subcommand prints as `line:column: message` (exit 1); optional keys still work through
  `if`, so data does not need placeholders for every field.
- A typo in an `if` (`{% if usre.admin %}`) is *not* caught: it is just false. This is the
  price of rule 2; `docs/template.md` says so.
- Rendering stops at the first error; no partial output is returned.
- `{% if x | lower %}` behaves differently from `{% if x %}` for `False`, `0` and `None`
  versus `""`; templates that test a value should test it without filters.
- Templates written for Jinja2's default mode that print optional keys need an `if` around
  them here.
- `tests/test_template_renderer.py` tests every row below and checks that its case list
  equals this table, so the two cannot drift apart. Cells are Python literals (a `|` is
  written `\x7c`); an outcome is the output, or `(error class name, line, column)`.

## Cases

| Template | Context | Outcome |
|----------|---------|---------|
| `'{{ name }}'` | `{'name': 'Ada'}` | `'Ada'` |
| `'Hi {{ name }}!'` | `{}` | `('TemplateError', 1, 4)` |
| `'{{ name \x7c upper }}'` | `{}` | `('TemplateError', 1, 1)` |
| `'{{ user.name }}'` | `{}` | `('TemplateError', 1, 1)` |
| `'{{ user.name }}'` | `{'user': {}}` | `('TemplateError', 1, 1)` |
| `'{{ user.name }}'` | `{'user': 'Ada'}` | `('TemplateError', 1, 1)` |
| `'{{ user.name }}'` | `{'user': None}` | `('TemplateError', 1, 1)` |
| `'a\n{{ b }}'` | `{}` | `('TemplateError', 2, 1)` |
| `'{% if name %}yes{% else %}no{% endif %}'` | `{}` | `'no'` |
| `'{% if user.admin %}yes{% else %}no{% endif %}'` | `{}` | `'no'` |
| `'{% if user.admin %}yes{% else %}no{% endif %}'` | `{'user': {}}` | `'no'` |
| `'{% if user.admin %}yes{% else %}no{% endif %}'` | `{'user': None}` | `('TemplateError', 1, 1)` |
| `'{% if name \x7c upper %}yes{% else %}no{% endif %}'` | `{}` | `'no'` |
| `'{% for x in items %}{{ x }}{% endfor %}'` | `{}` | `('TemplateError', 1, 1)` |
| `'{% for x in items %}{{ x.y }}{% endfor %}'` | `{'items': [{}]}` | `('TemplateError', 1, 21)` |
| `'{% for x in items %}{{ loop.size }}{% endfor %}'` | `{'items': [1]}` | `('TemplateError', 1, 21)` |
| `'[{{ x }}]'` | `{'x': None}` | `'[]'` |
| `'[{{ x \x7c upper }}]'` | `{'x': None}` | `'[]'` |
| `'{% if x %}yes{% else %}no{% endif %}'` | `{'x': None}` | `'no'` |
| `'{% for x in items %}{{ x }}{% endfor %}'` | `{'items': None}` | `('TemplateError', 1, 1)` |
| `'{% for x in items %}[{{ x }}]{% endfor %}'` | `{'items': [None, 'a']}` | `'[][a]'` |
| `'{{ x }}'` | `{'x': True}` | `'True'` |
| `'{{ x }}'` | `{'x': False}` | `'False'` |
| `'{{ x \x7c lower }}'` | `{'x': True}` | `'true'` |
| `'{% if x %}yes{% else %}no{% endif %}'` | `{'x': True}` | `'yes'` |
| `'{% if x %}yes{% else %}no{% endif %}'` | `{'x': False}` | `'no'` |
| `'{% if x \x7c lower %}yes{% else %}no{% endif %}'` | `{'x': False}` | `'yes'` |
| `'{{ n }}'` | `{'n': 0}` | `'0'` |
| `'{{ n }}'` | `{'n': -12}` | `'-12'` |
| `'{{ n }}'` | `{'n': 2.5}` | `'2.5'` |
| `'{% if n %}yes{% else %}no{% endif %}'` | `{'n': 0}` | `'no'` |
| `'{% if n %}yes{% else %}no{% endif %}'` | `{'n': 0.0}` | `'no'` |
| `'{% if n \x7c lower %}yes{% else %}no{% endif %}'` | `{'n': 0}` | `'yes'` |
| `'{% if s %}yes{% else %}no{% endif %}'` | `{'s': ''}` | `'no'` |
| `'{% if s %}yes{% else %}no{% endif %}'` | `{'s': '0'}` | `'yes'` |
| `'{% if xs %}yes{% else %}no{% endif %}'` | `{'xs': []}` | `'no'` |
