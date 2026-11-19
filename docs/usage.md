<!-- Usage guide of textkit (plan task T2.8): one short example per public function.
Every ">>>" block is a doctest that tests/test_usage.py runs, so the examples cannot drift
from the code. Doctest takes every non-blank line after a ">>>" line as expected output, so
each block keeps a blank line before its closing fence; without it the fence itself would
be expected output and the example would fail. -->
# Using textkit

`textkit` is a small package of text helpers: standard library only, Python 3.9+. Import
each function from its module. Every example below is run by `tests/test_usage.py`, so
what you read here is what the code does.

## Strings (`textkit.strings`)

`slugify` turns text into a lower-case ASCII slug. Characters outside ASCII are dropped,
not transliterated:

```python
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'
>>> slugify("Ñandú")
'and'

```

`strip_accents` removes combining marks, so it pairs well with `slugify`:

```python
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'
>>> slugify(strip_accents("Ñandú"))
'nandu'

```

`squeeze` collapses runs of whitespace into single spaces and strips both ends:

```python
>>> from textkit.strings import squeeze
>>> squeeze("  hello \n\t world  ")
'hello world'

```

`truncate` shortens text to a width; when it cuts, the result ends in the suffix and is
exactly `width` long:

```python
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hi", 8)
'Hi'
>>> truncate("Hello, World!", 6, suffix="~")
'Hello~'

```

`wrap` splits text into lines of at most `width` characters at spaces (existing newlines
are reflowed, ADR 0003):

```python
>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

`slug_title` is a slug cut to at most `max_len` characters that never ends in `-`:

```python
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'
>>> slug_title("Hello, World!", 6)
'hello'

```

`is_palindrome` ignores case, spaces, punctuation and accents:

```python
>>> from textkit.strings import is_palindrome
>>> is_palindrome("Anita lava la tina")
True
>>> is_palindrome("textkit")
False

```

## Counts (`textkit.counts`)

`word_count` follows the word rule of ADR 0001: hyphenated words, numbers and words with an
apostrophe count once each:

```python
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact: 42 words?")
6

```

`char_freq` counts each non-whitespace character, case-sensitive, in order of first
occurrence:

```python
>>> from textkit.counts import char_freq
>>> char_freq("Hello")
{'H': 1, 'e': 1, 'l': 2, 'o': 1}

```

`reading_time` estimates whole minutes, rounded up (ADR 0004), at `wpm=200` by default:

```python
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3
>>> reading_time("")
0

```

`sentence_count` knows common abbreviations and ellipses (ADR 0005):

```python
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He sat down... Then he left!")
3

```

## Identifier cases (`textkit.cases`)

`to_snake_case` splits runs of capitals as in ADR 0002:

```python
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'
>>> to_snake_case("parseURL2")
'parse_url2'

```

`to_camel_case` converts snake_case or kebab-case:

```python
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'
>>> to_camel_case("HTTP_server")
'httpServer'

```

`to_kebab_case` is built on `to_snake_case`:

```python
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("HTTPServer")
'http-server'

```

## Command line

Every public function with a single text argument is also a command (quote the text; a
`dict` or `list` result is printed as JSON):

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
$ python3 -m textkit char_freq "Hello"
{"H": 1, "e": 1, "l": 2, "o": 1}
$ python3 -m textkit --help       # lists every command
$ python3 -m textkit --version
textkit 0.1.0
```
