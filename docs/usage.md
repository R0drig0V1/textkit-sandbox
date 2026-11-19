<!-- Usage guide for textkit (plan task T2.8): one runnable example per public function. -->
# Using textkit

One short example per public function, grouped by module. Every `>>>` line below is a
[doctest](https://docs.python.org/3/library/doctest.html): `tests/test_usage.py` runs this
file, so `scripts/check.sh` goes red if an example stops matching the code. The same test
fails if a public function has no example here, so a new function needs one.

Rules behind the edge cases are in the ADRs (`docs/decisions/`); the full contract of each
function is in its docstring.

Writing an example: start it with `>>> from textkit.<module> import <function>`, put the
expected output right after the call, and leave a blank line before the closing fence
(doctest reads every line up to a blank one as expected output, the fence included).

## `textkit.cases`

`to_snake_case` splits runs of capitals as described in ADR 0001:

```pycon
>>> from textkit.cases import to_snake_case
>>> to_snake_case("parseURL2")
'parse_url2'

```

`to_kebab_case` is `to_snake_case` with `-` instead of `_`:

```pycon
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("HTTPServer")
'http-server'

```

`to_camel_case` goes the other way, from snake_case or kebab-case:

```pycon
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'

```

## `textkit.counts`

`word_count` counts hyphenated words, numbers and contractions as one word each (ADR 0002):

```pycon
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact: 42 is the answer.")
8

```

`sentence_count` keeps abbreviations and ellipses inside their sentence (ADR 0005):

```pycon
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. Wait... what? Yes!")
3

```

`reading_time` returns whole minutes, rounded up (ADR 0004); `wpm` defaults to 200:

```pycon
>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3
>>> reading_time("word " * 450, wpm=450)
1

```

`char_freq` skips whitespace, is case-sensitive and keeps keys in order of first occurrence:

```pycon
>>> from textkit.counts import char_freq
>>> char_freq("banana")
{'b': 1, 'a': 3, 'n': 2}

```

## `textkit.strings`

`slugify` keeps ASCII letters and digits only, joined by single `-`:

```pycon
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

```

`slug_title` cuts the slug to `max_len` characters and never ends in `-`:

```pycon
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'

```

`truncate` returns text that fits unchanged; otherwise the result, suffix included, is
exactly `width` long. A `width` shorter than the suffix raises `ValueError`:

```pycon
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hello", 8)
'Hello'

```

`strip_accents` removes combining marks:

```pycon
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

`squeeze` collapses runs of whitespace, newlines included, and strips both ends:

```pycon
>>> from textkit.strings import squeeze
>>> squeeze("  too   many\n spaces ")
'too many spaces'

```

`wrap` breaks between words; a word longer than `width` gets a line of its own (existing
newlines: ADR 0003):

```pycon
>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

`is_palindrome` ignores case, accents, spaces and punctuation:

```pycon
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá!")
True

```
