<!-- The textkit usage guide, plan task T2.8. Every ">>>" line below is run as a doctest by
tests/test_usage.py, which also checks that every public function is called here at least
once. Add an example when you add a public function. -->
# Usage guide

One short example per public function, grouped by module. Every example is a doctest: the
unit tests (`tests/test_usage.py`, run by `scripts/check.sh`) execute each `>>>` line and
compare its output with the line below it, so this page cannot drift from the code. The
full behaviour, edge cases and errors of each function are in its docstring; the README
function table lists them all.

## `textkit.strings`

Collapse whitespace, shorten text and reflow it into lines:

```python
>>> from textkit.strings import squeeze
>>> squeeze("  too   many\n spaces  ")
'too many spaces'

>>> from textkit.strings import truncate
>>> truncate("The quick brown fox", 10)
'The qui...'

>>> from textkit.strings import wrap
>>> wrap("The quick brown fox jumps", 10)
['The quick', 'brown fox', 'jumps']

```

Slugs, accents and palindromes:

```python
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'

>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panama")
True

```

## `textkit.counts`

Words follow ADR 0002, sentences ADR 0005, and reading time rounds up (ADR 0004):

```python
>>> from textkit.counts import word_count
>>> word_count("A well-known rule, don't you think?")
6

>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. Wait... what? Yes!")
3

>>> from textkit.counts import reading_time
>>> reading_time("word " * 201)
2

>>> from textkit.counts import char_freq
>>> char_freq("Hello")
{'H': 1, 'e': 1, 'l': 2, 'o': 1}

```

## `textkit.cases`

Identifier case conversion, with the word boundaries of ADR 0001:

```python
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'

>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'

>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("parseURL2")
'parse-url2'

```

The same functions are available from the shell; see [cli.md](cli.md).
