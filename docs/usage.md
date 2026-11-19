<!-- Usage guide (plan task T2.8). Every ">>>" example below is run by tests/test_usage.py,
     which also fails when a public function has no example here. -->
# Using textkit

One short example per public function, grouped by module. The examples are doctests:
`tests/test_usage.py` runs every one of them (through `scripts/check.sh`), so they always
match the code. Each function's docstring has the full behaviour and failure modes; the
rules that need a decision are in the ADRs under [`docs/decisions/`](decisions/README.md).

## `textkit.strings`

`slugify` lower-cases, drops characters outside ASCII and turns every other run of
non-alphanumeric characters into one `-`:

```pycon
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

```

`slug_title` is a slug cut to at most `max_len` characters that never ends in `-`:

```pycon
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'
>>> slug_title("Hello, World!", 6)
'hello'

```

`truncate` cuts text to exactly `width` characters, suffix included:

```pycon
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hello", 8)
'Hello'

```

`squeeze` collapses runs of whitespace into single spaces and strips both ends:

```pycon
>>> from textkit.strings import squeeze
>>> squeeze("  lots   of \t space \n here ")
'lots of space here'

```

`strip_accents` removes combining marks:

```pycon
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

`is_palindrome` ignores case, accents, spaces and punctuation:

```pycon
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá!")
True
>>> is_palindrome("textkit")
False

```

`wrap` splits text into lines of at most `width` characters at spaces (existing newlines
are separators too, ADR 0003):

```pycon
>>> from textkit.strings import wrap
>>> wrap("The quick brown fox jumps over the lazy dog", 10)
['The quick', 'brown fox', 'jumps over', 'the lazy', 'dog']

```

## `textkit.cases`

The three case converters split words the same way (ADR 0002), so runs of capitals such as
`HTTP` stay one word:

```pycon
>>> from textkit.cases import to_camel_case, to_kebab_case, to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'
>>> to_kebab_case("userId")
'user-id'
>>> to_camel_case("max_retry_count")
'maxRetryCount'

```

## `textkit.counts`

`word_count` follows the word rule of ADR 0001: a hyphen or apostrophe between letters joins
them, other punctuation separates:

```pycon
>>> from textkit.counts import word_count
>>> word_count("Hello, world! It's a well-known fact.")
6

```

`sentence_count` does not end a sentence at a known title such as `Dr.` or at an ellipsis
followed by a lower-case word (ADR 0005):

```pycon
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He waited... Then he left!")
3

```

`reading_time` gives whole minutes at `wpm` words per minute (200 by default), rounded up
(ADR 0004):

```pycon
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3
>>> reading_time("word " * 450, wpm=500)
1

```

`char_freq` counts each non-whitespace character, case-sensitive; the dictionary keeps the
order of first occurrence, so its output is deterministic:

```pycon
>>> from textkit.counts import char_freq
>>> char_freq("Hello hi")
{'H': 1, 'e': 1, 'l': 2, 'o': 1, 'h': 1, 'i': 1}

```

## Command line

`python3 -m textkit <function> "<text>"` prints the result of any public function that takes
one text argument; parameters with defaults keep them, so `truncate` and `wrap` (which need a
`width`) are not commands. Strings print as they are, lists and dictionaries as JSON (keys
sorted), and other values such as `True` or `3` as Python prints them. Text that starts with
`-` goes after `--`.

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
$ python3 -m textkit word_count "It's a well-known fact."
4
```

`python3 -m textkit --help` lists the commands with a one-line summary each, and
`python3 -m textkit --version` prints `textkit <version>`. Usage errors (an unknown function,
a missing or extra argument) exit with status 2 and the message on standard error.
