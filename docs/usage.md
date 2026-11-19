<!-- Usage guide of textkit (plan task T2.8): one runnable example per public function.
     Every ">>>" block is a doctest run by tests/test_usage.py, so a wrong example fails
     scripts/check.sh. Keep a blank line before each closing fence: doctest reads the expected
     output up to the first blank line, and would otherwise expect the fence itself. -->
# Using textkit

`textkit` is a set of plain functions: import the one you need from its module and call it.
Every example below is executed by `tests/test_usage.py`, so what you read is what you get.
The README function table lists the same functions with one-line summaries.

## `textkit.strings`

### `squeeze`

Collapses every run of whitespace (newlines included) into one space and strips both ends.

```python
>>> from textkit.strings import squeeze
>>> squeeze("  hello   big \n world ")
'hello big world'

```

### `slugify`

Lower-cased ASCII slug; every run of other characters becomes one `-`, and characters
outside ASCII are dropped (strip the accents first to keep their letters).

```python
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

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

### `strip_accents`

Removes combining marks such as accents and tildes.

```python
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

### `truncate`

Returns the text unchanged when it fits; otherwise cuts it so that the result, suffix
included, is exactly `width` long. A `width` shorter than the suffix raises `ValueError`.

```python
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hello, World!", 8, suffix="")
'Hello, W'

```

### `wrap`

Splits text into lines of at most `width` characters at spaces (ADR 0003 on newlines).

```python
>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

### `is_palindrome`

Ignores case, accents, spaces and punctuation; digits count.

```python
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá")
True
>>> is_palindrome("textkit")
False

```

## `textkit.counts`

### `word_count`

Counts words by the rule of ADR 0002: hyphenated words, numbers and contractions are one
word each.

```python
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact: 42 is the answer.")
8

```

### `char_freq`

Counts each non-whitespace character, case-sensitive, in order of first occurrence.

```python
>>> from textkit.counts import char_freq
>>> char_freq("hello")
{'h': 1, 'e': 1, 'l': 2, 'o': 1}

```

### `reading_time`

Whole minutes at `wpm` words per minute (200 by default), rounded up (ADR 0004).

```python
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3
>>> reading_time("word " * 450, wpm=450)
1

```

### `sentence_count`

Counts sentences; abbreviations such as `Dr.` and ellipses are handled by ADR 0005.

```python
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He said hello... Then he left!")
3

```

## `textkit.cases`

### `to_snake_case`

From camelCase, PascalCase or kebab-case; runs of capitals are split by ADR 0001.

```python
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'
>>> to_snake_case("parseURL2")
'parse_url2'

```

### `to_camel_case`

From snake_case or kebab-case.

```python
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'

```

### `to_kebab_case`

From camelCase, PascalCase or snake_case, built on `to_snake_case`.

```python
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("parseURL2")
'parse-url2'

```

## Command line

Every function that takes one text argument also runs from the shell; quote the text.
`str` results print as they are, `dict` and `list` results as JSON with sorted keys.
(These lines are shell, not doctest, so the test does not run them; `tests/test_cli.py`
covers the command line.)

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
$ python3 -m textkit char_freq "hello"
{"e": 1, "h": 1, "l": 2, "o": 1}
```

`python3 -m textkit --help` lists every command with the first line of its docstring, and
`python3 -m textkit --version` prints `textkit <version>` (`textkit.__version__`).
