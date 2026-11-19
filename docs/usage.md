# Usage guide

One short example per public function of `textkit`, grouped by module. Every example is a
doctest: `tests/test_usage.py` runs this file with `doctest` as part of `scripts/check.sh`,
and fails if a public function is missing from it, so the guide cannot drift from the code.
The full behaviour and failure modes of each function are in its docstring; the README
function table is the index.

Examples that return a `dict` or a `list` show the value exactly as the function orders it,
so doctest compares them literally.

To add an example, keep the `>>> from textkit.<module> import <f>` line first and leave a
blank line before the closing code fence: doctest reads every line after a `>>>` line, up
to a blank one, as expected output, the fence included.

## `textkit.cases`

```python
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'

>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("HTTPServer")
'http-server'

>>> from textkit.cases import to_snake_case
>>> to_snake_case("parseURL2")
'parse_url2'

```

Capital runs are split as decided in
[0003-snake-case-capital-runs](decisions/0003-snake-case-capital-runs.md).

## `textkit.ciphers`

```python
>>> from textkit.ciphers import rot13
>>> rot13("Hello, World!")
'Uryyb, Jbeyq!'
>>> rot13(rot13("Hello, World!"))
'Hello, World!'

```

## `textkit.counts`

```python
>>> from textkit.counts import char_freq
>>> char_freq("hello")
{'h': 1, 'e': 1, 'l': 2, 'o': 1}

>>> from textkit.counts import reading_time
>>> reading_time("word " * 201)
2

>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith paid 3.14 dollars. Really?! Yes.")
3

>>> from textkit.counts import word_count
>>> word_count("A well-known fact: don't panic.")
5

```

`char_freq` keys come in order of first occurrence. The rules are in
[0002-what-counts-as-a-word](decisions/0002-what-counts-as-a-word.md),
[0004-reading-time-rounding](decisions/0004-reading-time-rounding.md) and
[0005-sentence-boundaries](decisions/0005-sentence-boundaries.md).

## `textkit.distance`

```python
>>> from textkit.distance import levenshtein
>>> levenshtein("kitten", "sitting")
3

```

## `textkit.durations`

```python
>>> from textkit.durations import parse_duration
>>> parse_duration("1h30m")
5400
>>> parse_duration("1h 30m")
Traceback (most recent call last):
    ...
ValueError: parse_duration() expects a duration such as '1h30m', got '1h 30m'

```

## `textkit.emails`

```python
>>> from textkit.emails import is_email
>>> is_email("ada@example.com")
True
>>> is_email("ada@localhost")
False

```

Only the syntax is checked, with no network access
([0006-what-is-an-email-address](decisions/0006-what-is-an-email-address.md)).

## `textkit.names`

```python
>>> from textkit.names import initials
>>> initials("jean-luc picard")
'JLP'

```

## `textkit.numwords`

```python
>>> from textkit.numwords import number_to_words
>>> number_to_words(42)
'forty-two'

```

## `textkit.ordinals`

```python
>>> from textkit.ordinals import ordinal
>>> [ordinal(n) for n in (1, 2, 3, 11, 112)]
['1st', '2nd', '3rd', '11th', '112th']

```

## `textkit.phonetic`

```python
>>> from textkit.phonetic import soundex
>>> soundex("Robert"), soundex("Rupert")
('R163', 'R163')

```

## `textkit.plural`

```python
>>> from textkit.plural import pluralize
>>> pluralize("city"), pluralize("Child")
('cities', 'Children')

```

The rules are in [0007-pluralize-rules](decisions/0007-pluralize-rules.md).

## `textkit.roman`

```python
>>> from textkit.roman import to_roman
>>> to_roman(1994)
'MCMXCIV'

```

## `textkit.sizes`

```python
>>> from textkit.sizes import human_bytes
>>> human_bytes(1536)
'1.5 KiB'

```

## `textkit.strings`

```python
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá")
True

>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 6)
'hello'

>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

>>> from textkit.strings import squeeze
>>> squeeze("  too   many\tspaces ")
'too many spaces'

>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'

>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

`wrap` reflows existing line breaks
([0001-wrap-reflows-existing-newlines](decisions/0001-wrap-reflows-existing-newlines.md)).

## `textkit.templates`

```python
>>> from textkit.templates import render
>>> render("Hi {name}, {{literal}}", {"name": "Ada"})
'Hi Ada, {literal}'

```
