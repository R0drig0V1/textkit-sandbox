<!-- Usage guide (plan task T2.8): one runnable example per public function, checked by tests/test_usage.py. -->
# Using textkit

One short example per public function, grouped by module. Every `>>>` block on this page is
a doctest: `tests/test_usage.py` runs them all as part of `scripts/check.sh`, and fails if a
public function has no example here. When you add a public function, add its example below
(the test tells you which ones are missing).

Each example imports its own function, so any block can be pasted into a Python 3.9+
session on its own. The full behaviour and failure modes of each function are in its
docstring (`help(textkit.<module>.<function>)`), and the README function table lists them
all.

## `textkit.cases`: identifier case conversion

```pycon
>>> from textkit.cases import to_snake_case
>>> to_snake_case("parseHTTPResponse")
'parse_http_response'

>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("parseHTTPResponse")
'parse-http-response'

>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_name")
'userName'

```

Acronyms stay whole (ADR 0001); `to_kebab_case` uses the same word rules as
`to_snake_case`.

## `textkit.ciphers`: letter rotation

```pycon
>>> from textkit.ciphers import rot13
>>> rot13("Hello, World!")
'Uryyb, Jbeyq!'
>>> rot13(rot13("Hello, World!"))
'Hello, World!'

```

## `textkit.counts`: counting words, sentences and characters

```pycon
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact, 42 times over.")
7

>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He sat down... and waited. Why?")
3

>>> from textkit.counts import reading_time
>>> reading_time("word " * 450)
3

>>> from textkit.counts import char_freq
>>> char_freq("hello")
{'h': 1, 'e': 1, 'l': 2, 'o': 1}

```

Hyphenated words, contractions and numbers count as one word (ADR 0002); abbreviations and
mid-sentence ellipses do not end a sentence (ADR 0007); `reading_time` rounds up to whole
minutes at 200 words per minute by default (ADR 0006).

## `textkit.distance`: edit distance

```pycon
>>> from textkit.distance import levenshtein
>>> levenshtein("kitten", "sitting")
3

```

## `textkit.durations`: parsing durations

```pycon
>>> from textkit.durations import parse_duration
>>> parse_duration("1h30m")
5400
>>> parse_duration("90 minutes")
Traceback (most recent call last):
    ...
ValueError: not a duration: '90 minutes'

```

## `textkit.emails`: e-mail syntax

```pycon
>>> from textkit.emails import is_email
>>> is_email("ada@example.com")
True
>>> is_email("not an email")
False

```

The check is syntactic and offline (ADR 0003): no DNS lookup, no delivery.

## `textkit.names`: initials

```pycon
>>> from textkit.names import initials
>>> initials("Jean-Luc picard")
'JLP'

```

## `textkit.numwords`: numbers in words

```pycon
>>> from textkit.numwords import number_to_words
>>> number_to_words(42)
'forty-two'

```

## `textkit.ordinals`: ordinal suffixes

```pycon
>>> from textkit.ordinals import ordinal
>>> ordinal(21), ordinal(11)
('21st', '11th')

```

## `textkit.phonetic`: Soundex

```pycon
>>> from textkit.phonetic import soundex
>>> soundex("Robert")
'R163'

```

## `textkit.plural`: plurals

```pycon
>>> from textkit.plural import pluralize
>>> pluralize("city"), pluralize("child")
('cities', 'children')

```

The rules and irregulars are in ADR 0004.

## `textkit.roman`: Roman numerals

```pycon
>>> from textkit.roman import to_roman
>>> to_roman(1994)
'MCMXCIV'

```

## `textkit.sizes`: byte counts

```pycon
>>> from textkit.sizes import human_bytes
>>> human_bytes(1536)
'1.5 KiB'

```

## `textkit.strings`: slugs, whitespace, accents and line breaking

```pycon
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

>>> from textkit.strings import slug_title
>>> slug_title("Hello, World and Everyone", 12)
'hello-world'

>>> from textkit.strings import squeeze
>>> squeeze("  too   many\n spaces ")
'too many spaces'

>>> from textkit.strings import strip_accents
>>> strip_accents("Crème brûlée")
'Creme brulee'

>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá")
True

>>> from textkit.strings import truncate
>>> truncate("Hello, world", 8)
'Hello...'

>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

`slug_title` drops the `-` the cut would leave at the end; `wrap` reflows existing newlines
as spaces (ADR 0005).

## `textkit.templates`: placeholders

```pycon
>>> from textkit.templates import render
>>> render("Hi {name}, {{literal}}", {"name": "Ada"})
'Hi Ada, {literal}'

```

## Command line

Every public function with exactly one required parameter is also a command (see the
`textkit/__main__.py` docstring for the exit codes and argument rules):

```bash
python3 -m textkit slugify "Hello, World!"     # hello-world
python3 -m textkit to_roman 1994               # MCMXCIV
python3 -m textkit --help                      # every command and its summary
python3 -m textkit --version                   # textkit 0.1.0
```
