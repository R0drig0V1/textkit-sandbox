<!-- Usage guide for textkit: one example per public function, plus the command line.
     Every ">>>" example below is run as a doctest by tests/test_usage.py (plan task T2.8),
     which also checks that every public function is called in at least one ">>>" line, so
     an example that drifts from the code, or a new function with no example, turns
     scripts/check.sh red. -->
# Using textkit

`textkit` is a small package of text helpers: standard library only, Python 3.9+. Each
section below shows one public function in action, grouped by module. The examples are
doctests: `tests/test_usage.py` runs every one of them, so what you read here is what the
code returns. The full rules live in the docstrings and, where noted, in the ADRs under
[`docs/decisions/`](decisions/README.md).

## Strings (`textkit.strings`)

### `slugify`

Lower-case ASCII slug; characters outside ASCII are dropped, not transliterated.

```python
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'
>>> slugify("naïve")
'nave'

```

### `slug_title`

A slug cut to at most `max_len` characters that never ends in `-`.

```python
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'
>>> slug_title("Hello, World!", 6)
'hello'

```

### `truncate`

Shortens text to exactly `width` characters, suffix included; text that fits is returned
unchanged.

```python
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hi", 8)
'Hi'
>>> truncate("Hello", 2)
Traceback (most recent call last):
    ...
ValueError: width (2) is smaller than the suffix length (3)

```

### `squeeze`

Collapses runs of whitespace into single spaces and strips both ends.

```python
>>> from textkit.strings import squeeze
>>> squeeze("  too   many\n spaces ")
'too many spaces'

```

### `strip_accents`

Removes combining marks; letters with no decomposition (`ø`, `ß`) are kept.

```python
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

### `wrap`

Greedy line wrapping at spaces; existing newlines are reflowed (ADR 0003) and a word longer
than `width` gets a line of its own.

```python
>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

### `is_palindrome`

Ignores case, spaces, punctuation and accents.

```python
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panama")
True
>>> is_palindrome("textkit")
False

```

## Counts (`textkit.counts`)

### `word_count`

Hyphenated words, contractions and numbers such as `3.14` count once (ADR 0002).

```python
>>> from textkit.counts import word_count
>>> word_count("A well-known fact: pi is 3.14, isn't it?")
8

```

### `char_freq`

Counts each non-whitespace character, case-sensitive, keys in order of first occurrence.

```python
>>> from textkit.counts import char_freq
>>> char_freq("banana")
{'b': 1, 'a': 3, 'n': 2}

```

### `reading_time`

Whole minutes at `wpm` words per minute (default 200), rounded up (ADR 0004).

```python
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3
>>> reading_time("")
0

```

### `sentence_count`

Abbreviations such as `Dr.` and `e.g.` do not end a sentence; an ellipsis does only before a
capital (ADR 0005).

```python
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He sat down... and waited. Done!")
3

```

## Identifier cases (`textkit.cases`)

### `to_snake_case`

Runs of capitals stay one word; digits stay with the word before them (ADR 0001).

```python
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'
>>> to_snake_case("parseURL2")
'parse_url2'

```

### `to_camel_case`

```python
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'
>>> to_camel_case("HTTP_server")
'httpServer'

```

### `to_kebab_case`

```python
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("HTTPServer")
'http-server'

```

## Command line

`python3 -m textkit <function> <text>` runs a function on one text and prints the result.
Every public function with exactly one required parameter is a command (functions that need
more, such as `truncate`, `wrap` and `slug_title`, are not); parameters with a default keep
it, so `reading_time` runs with `wpm=200`. Quote the text so it reaches the command as one
argument. These examples are plain shell sessions, not doctests:

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
$ python3 -m textkit is_palindrome "A man, a plan, a canal: Panama"
True
$ python3 -m textkit char_freq banana
{"a": 3, "b": 1, "n": 2}
$ python3 -m textkit word_count -- -x
1
$ python3 -m textkit --version
textkit 0.1.0
```

- A `str` result is printed as is, `bool` and `int` with `print()`, and a `dict` or `list` as
  JSON with sorted keys (`json.dumps(result, ensure_ascii=False, sort_keys=True)`).
- A text that starts with `-` goes after `--`, as in the `word_count` example.
- `python3 -m textkit --help` lists every command with the first line of its docstring.
- `python3 -m textkit --version` prints `textkit` and the package version
  (`textkit.__version__`).
- Exit status: 0 on success; 2 (message on stderr) for an unknown function, a wrong number
  of arguments or no arguments at all; 1 (message on stderr) if the function raises
  `ValueError` or `TypeError`.
