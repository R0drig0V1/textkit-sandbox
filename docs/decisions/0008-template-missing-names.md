<!-- ADR 0008: what textkit.template.render does with a name missing from the context (plan task T3.4). -->
# 0008. Names missing from a template's context: an error, except in `if`

Status: accepted (plan task T3.4)

## Context

`textkit.template.render(template, context)` looks names up in a dict. A template can name a
key that the context does not have: `{{ nmae }}` (a typo), `{{ user.nickname }}` (an
optional key), `{% for x in items %}` with no `items`. Engines answer this in two ways:

- **empty text** (Jinja's default `Undefined`, Mustache): the template always renders, and
  a typo silently prints nothing. The bug shows up later, in the output, if at all;
- **an error** (Jinja's `StrictUndefined`, Go's `missingkey=error`): typos fail at once, but
  a template cannot even ask whether an optional key is there.

Related questions the same rule must settle: what `None` prints (JSON `null` reaches the
context through the `render` subcommand), how booleans and numbers print, and what a
dotted name does when a part is present but is not a dict.

## Decision

1. **`{{ name }}` with a missing name is a `TemplateError`**, at the position of its `{{`.
   This covers a missing first part (`name 'x' is not defined`) and a missing key further
   along (`'user' has no key 'name'`). A typo fails on the first render that reaches it.
2. **`{% for x in name %}` with a missing name is a `TemplateError`** too, at its `{%`: a
   loop over nothing is more likely a typo than an intent. An empty list is the way to say
   "no items".
3. **`{% if name %}` with a missing name is false**, wherever the missing part is
   (`{% if user.nickname %}` is false when `user` has no `nickname` and when there is no
   `user`). `if` is how a template asks "is it there?", so it must be able to ask about a
   missing key; the `else` branch, if any, renders. The filters of a missing name are not
   applied. Only the `if` test is lenient: an `{{ }}` inside the true branch still fails
   when it is rendered and its name is missing.
4. **A dotted name through a value that is not a dict is a `TemplateError` everywhere**,
   `if` included (`user.name` when `user` is `"Ada"` or `None`). That is not a missing key
   but a context of the wrong shape, which leniency would hide.
5. **`None` prints as `""`**; filters then apply to `""`. In `if`, `None` is false. So a
   key that is present with value `None` is the way to say "known, but empty", and it never
   fails, unlike a missing key.
6. **Every other value prints as `str(value)`**: `True` and `False` (not `true`/`false`),
   `42`, `0`, `1.5`. Filters apply to that text, so `{{ f | lower }}` prints `false`.
7. **Truth is Python's `bool` of the value**: `0`, `0.0`, `""`, `[]`, `{}`, `None` and
   `False` are false; `"0"` and `-1` are true. With filters, it is the `bool` of the
   filtered text, so `{% if f | lower %}` is true for `False` (`"false"` is not empty).
8. **A value is never rendered again**: a context value `"{{ y }}"` prints as is.

## Consequences

- Typos in output and loops fail loudly, with a line and column; optional keys are handled
  with `if`, the idiom the template author already reaches for.
- A template that prints an optional key must guard it:
  `{% if user.nickname %}{{ user.nickname }}{% endif %}`. There is no default filter; one
  could be added later without changing this rule.
- A syntax error is reported whatever the context, because the whole template is parsed
  before anything is rendered: a missing name in an `if` never hides a bad filter.
- The `render` subcommand inherits the rule: JSON `null` prints as empty text, a missing key
  exits 1 with `line:column: message`.
- `tests/test_template_renderer.py` finds this ADR by its slug, parses the table below with
  `ast.literal_eval` and checks that its own case list equals it and that `render` gives
  every outcome, so the table and the code cannot drift apart.

## Cases

Each cell is a Python literal. The outcome is the output, or the error class name with the
line and column of the tag at fault. A `|` in a template is written `\x7c`.

| Template | Context | Outcome |
|----------|---------|---------|
| `"Hello {{ name }}!"` | `{"name": "Ada"}` | `"Hello Ada!"` |
| `"Hello {{ name }}!"` | `{}` | `("TemplateError", 1, 7)` |
| `"{{ user.name }}"` | `{"user": {}}` | `("TemplateError", 1, 1)` |
| `"{{ user.name }}"` | `{"user": "Ada"}` | `("TemplateError", 1, 1)` |
| `"{{ user.name }}"` | `{"user": None}` | `("TemplateError", 1, 1)` |
| `"[{{ x }}]"` | `{"x": None}` | `"[]"` |
| `"[{{ x \x7c upper }}]"` | `{"x": None}` | `"[]"` |
| `"[{{ x }}]"` | `{"x": ""}` | `"[]"` |
| `"{{ t }} {{ f }}"` | `{"t": True, "f": False}` | `"True False"` |
| `"{{ f \x7c lower }}"` | `{"f": False}` | `"false"` |
| `"{{ n }} {{ z }} {{ r }}"` | `{"n": 42, "z": 0, "r": 1.5}` | `"42 0 1.5"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": None}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": False}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": True}` | `"y"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": 0}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": 0.0}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": -1}` | `"y"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": ""}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": "0"}` | `"y"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": []}` | `"n"` |
| `"{% if x %}y{% else %}n{% endif %}"` | `{"x": {}}` | `"n"` |
| `"{% if user.name %}y{% else %}n{% endif %}"` | `{}` | `"n"` |
| `"{% if user.name %}y{% else %}n{% endif %}"` | `{"user": {}}` | `"n"` |
| `"{% if user.name %}y{% else %}n{% endif %}"` | `{"user": "Ada"}` | `("TemplateError", 1, 1)` |
| `"{% if user.name %}y{% else %}n{% endif %}"` | `{"user": None}` | `("TemplateError", 1, 1)` |
| `"{% if x \x7c lower %}y{% else %}n{% endif %}"` | `{"x": False}` | `"y"` |
| `"{% if x \x7c lower %}y{% else %}n{% endif %}"` | `{}` | `"n"` |
| `"{% if x %}{{ y }}{% endif %}"` | `{}` | `""` |
| `"{% if x %}{{ y }}{% endif %}"` | `{"x": 1}` | `("TemplateError", 1, 11)` |
| `"{% if x %}{{ y \x7c nope }}{% endif %}"` | `{}` | `("TemplateSyntaxError", 1, 11)` |
| `"{% for i in xs %}{{ i }}{% endfor %}"` | `{}` | `("TemplateError", 1, 1)` |
| `"{% for i in xs %}{{ i }}{% endfor %}"` | `{"xs": None}` | `("TemplateError", 1, 1)` |
| `"{% for i in xs %}{{ i }}{% endfor %}"` | `{"xs": "ab"}` | `("TemplateError", 1, 1)` |
| `"{% for i in xs %}{{ i }}{% endfor %}"` | `{"xs": []}` | `""` |
| `"{% for i in xs %}{{ i }}{% endfor %}"` | `{"xs": [1, None, True, 2.5]}` | `"1True2.5"` |
| `"{% for i in xs %}{{ loop.index }}{% endfor %}{{ loop }}"` | `{"xs": ["a", "b"], "loop": "L"}` | `"12L"` |
| `"{{ loop.index }}"` | `{}` | `("TemplateError", 1, 1)` |
| `"a\n{{ b }}"` | `{}` | `("TemplateError", 2, 1)` |
| `"a\r\n  {{ b }}"` | `{}` | `("TemplateError", 2, 3)` |
| `"a\r{{ b }}"` | `{}` | `("TemplateError", 1, 3)` |
| `"{{ x }}"` | `{"x": "{{ y }}"}` | `"{{ y }}"` |
