<!-- Usage guide of textkit (plan task T2.8): one short example per public function. Every
example is a doctest that tests/test_usage.py runs, and that test fails if a public function
has no example here. -->
# Using textkit

Each section shows one public function with a short example. The examples are doctests:
`tests/test_usage.py` runs them all (so `scripts/check.sh` goes red if one stops matching the
code) and checks that every public function is called in at least one `>>>` line. When you
add a public function, add a section here in the same pull request.

The rules behind the less obvious results are in the ADRs under
[`docs/decisions/`](decisions/README.md).

## `textkit.strings`

### `slugify`

Lower-case ASCII slug; characters outside ASCII are dropped, not transliterated.

```pycon
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

```

### `slug_title`

A slug cut to at most `max_len` characters that never ends in `-`.

```pycon
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 6)
'hello'

```

### `truncate`

The result, suffix included, is exactly `width` long; a width smaller than the suffix is an
error even when the text would fit.

```pycon
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hi", 2)
Traceback (most recent call last):
    ...
ValueError: width (2) is smaller than the suffix length (3)

```

### `strip_accents`

```pycon
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

### `squeeze`

```pycon
>>> from textkit.strings import squeeze
>>> squeeze("  too   many\n spaces ")
'too many spaces'

```

### `wrap`

Breaks at spaces; existing newlines are treated as spaces (ADR 0003).

```pycon
>>> from textkit.strings import wrap
>>> wrap("The quick brown fox jumps", 10)
['The quick', 'brown fox', 'jumps']

```

### `is_palindrome`

Ignores case, spaces, punctuation and accents.

```pycon
>>> from textkit.strings import is_palindrome
>>> is_palindrome("Anita lava la tina")
True

```

## `textkit.counts`

### `word_count`

Hyphenated words, numbers and words with an apostrophe count once each (ADR 0001).

```pycon
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact: 42 apples.")
6

```

### `char_freq`

Case-sensitive, whitespace not counted, keys in order of first occurrence.

```pycon
>>> from textkit.counts import char_freq
>>> char_freq("banana")
{'b': 1, 'a': 3, 'n': 2}

```

### `reading_time`

Whole minutes, rounded up (ADR 0004): 450 words at the default 200 words per minute.

```pycon
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3

```

### `sentence_count`

Titles such as `Dr.` and ellipses do not end a sentence on their own (ADR 0005).

```pycon
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. Wait... what?")
2

```

## `textkit.cases`

### `to_snake_case`

A run of capitals is one word (ADR 0002).

```pycon
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'

```

### `to_kebab_case`

```pycon
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("parseURL2")
'parse-url2'

```

### `to_camel_case`

```pycon
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'

```

## Command line

Every public function of one text argument is also a command (quote the text):

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
$ python3 -m textkit --help
```

`tests/test_cli.py` covers the command line; the blocks above are what this page tests.
