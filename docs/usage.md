<!-- Usage guide for textkit: one short, runnable example per public function. -->
# Usage guide

One short example per public function, grouped by module. Every `>>>` block on this page is
a doctest: `tests/test_usage.py` runs the whole file (so `scripts/check.sh` goes red if an
example stops matching the code) and checks that every public function is called in at
least one example. When you add a public function, add its example here.

The rules behind some results are ADRs in [`decisions/`](decisions/README.md).

## `textkit.strings`

`slugify` lower-cases and keeps ASCII letters and digits, one `-` between runs:

```python
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

```

`slug_title` is a slug cut to at most `max_len` characters, never ending in `-`:

```python
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'

```

`truncate` cuts text to a width, the suffix included:

```python
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'

```

`strip_accents` removes combining marks:

```python
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

`wrap` splits text into lines of at most a width, at spaces (existing newlines: ADR 0003):

```python
>>> from textkit.strings import wrap
>>> wrap("the quick brown fox", 10)
['the quick', 'brown fox']

```

`squeeze` collapses every run of whitespace into one space:

```python
>>> from textkit.strings import squeeze
>>> squeeze("  a \t b\n\nc  ")
'a b c'

```

`is_palindrome` ignores case, spaces, punctuation and accents:

```python
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá")
True
>>> is_palindrome("textkit")
False

```

## `textkit.counts`

`word_count` counts words; hyphenated words, numbers and apostrophes follow ADR 0001:

```python
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact: 42 words.")
6

```

`char_freq` counts each non-whitespace character, keys in order of first occurrence:

```python
>>> from textkit.counts import char_freq
>>> char_freq("hello")
{'h': 1, 'e': 1, 'l': 2, 'o': 1}

```

`reading_time` gives whole minutes at `wpm` words per minute (default 200), rounded up
(ADR 0004):

```python
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3

```

`sentence_count` does not end a sentence at abbreviations such as `Dr.` (ADR 0005):

```python
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He waited... Then he left!")
3

```

## `textkit.cases`

`to_snake_case` splits runs of capitals as in ADR 0002:

```python
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'

```

`to_camel_case` converts snake_case or kebab-case:

```python
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'

```

`to_kebab_case` is `to_snake_case` with `-` instead of `_`:

```python
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("parseURL2")
'parse-url2'

```

## Command line

Every public function of one text argument also runs from the shell (not a doctest):

```bash
python3 -m textkit slugify "Hello, World!"     # hello-world
python3 -m textkit --help                      # lists the commands
python3 -m textkit --version                   # textkit 0.1.0
```
