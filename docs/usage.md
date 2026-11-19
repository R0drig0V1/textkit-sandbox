# Usage guide

One short example per public textkit function, and a few command line runs. Every example
on this page is run by `tests/test_usage.py` (part of `scripts/check.sh`), so the outputs
shown are the real ones.

How to add or change an example (the test enforces each rule):

- Each public function has one `###` heading holding its qualified name in backticks
  (`` `textkit.<module>.<function>` ``), with at least one `pycon` block below it that calls
  the function. A public function without such a section, or a heading naming a function
  that does not exist, fails the test.
- A `pycon` block is a doctest session: `>>>` lines and their exact output. Each block runs
  on its own, so it starts with its own import.
- A `console` block holds only `$ python3 -m textkit ...` commands, each followed by its
  exact standard output. No pipes or other shell syntax: the test runs the command itself.
- No other fenced blocks: an example the test cannot run is not allowed on this page.

## Strings

### `textkit.strings.squeeze`

Collapses every run of whitespace (tabs and line breaks included) into one space and trims
the ends.

```pycon
>>> from textkit.strings import squeeze
>>> squeeze("  too   many\t\tspaces \n")
'too many spaces'
```

### `textkit.strings.slugify`

An ASCII lower-case slug joined by `-`. Non-ASCII characters are dropped, not transliterated;
use `strip_accents` first to keep accented letters.

```pycon
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'
>>> slugify("Crème brûlée")
'crme-brle'
```

### `textkit.strings.truncate`

Shortens text to exactly `width` characters, the suffix included.

```pycon
>>> from textkit.strings import truncate
>>> truncate("The quick brown fox", 10)
'The qui...'
```

### `textkit.strings.strip_accents`

Removes combining marks.

```pycon
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú café")
'Nandu cafe'
```

### `textkit.strings.wrap`

Splits text into lines of at most `width` characters, breaking at whitespace.

```pycon
>>> from textkit.strings import wrap
>>> wrap("The quick brown fox jumps", 10)
['The quick', 'brown fox', 'jumps']
```

### `textkit.strings.slug_title`

A slug of at most `max_len` characters, cut at a word boundary rather than mid-word.

```pycon
>>> from textkit.strings import slug_title
>>> slug_title("Hello World Again", 12)
'hello-world'
```

### `textkit.strings.is_palindrome`

Ignores case, accents, spaces and punctuation.

```pycon
>>> from textkit.strings import is_palindrome
>>> is_palindrome("A man, a plan, a canal: Panamá")
True
```

## Counts

### `textkit.counts.word_count`

Hyphenated words, contractions and numbers count once
([ADR 0001](decisions/0001-what-counts-as-a-word.md)).

```pycon
>>> from textkit.counts import word_count
>>> word_count("It's a well-known fact: 3 cats.")
6
```

### `textkit.counts.char_freq`

Counts each non-whitespace character, case-sensitive, in order of first appearance.

```pycon
>>> from textkit.counts import char_freq
>>> char_freq("banana")
{'b': 1, 'a': 3, 'n': 2}
```

### `textkit.counts.sentence_count`

Abbreviations such as `Dr.` do not end a sentence
([ADR 0004](decisions/0004-where-a-sentence-ends.md)).

```pycon
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. Was it late? Yes!")
3
```

### `textkit.counts.reading_time`

Whole minutes at `wpm` words per minute (200 by default), rounded up: 201 words take 2
minutes ([ADR 0005](decisions/0005-reading-time-rounding.md)).

```pycon
>>> from textkit.counts import reading_time
>>> reading_time("word " * 201)
2
```

## Cases

### `textkit.cases.to_snake_case`

Acronyms stay whole ([ADR 0002](decisions/0002-snake-case-word-boundaries.md)).

```pycon
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'
```

### `textkit.cases.to_camel_case`

Splits words as `to_snake_case` does, so PascalCase and acronyms are normalised too.

```pycon
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'
>>> to_camel_case("HTTPServer")
'httpServer'
```

### `textkit.cases.to_kebab_case`

Splits words as `to_snake_case` does, joined with `-`.

```pycon
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("parseURL")
'parse-url'
```

## Command line

`python3 -m textkit <function> <text>` runs any function that takes one text; see the
[README](../README.md#command-line) for the full rules. A `bool` prints as `true`/`false`.

```console
$ python3 -m textkit slugify "Hello, World!"
hello-world
$ python3 -m textkit is_palindrome "Never odd or even"
true
$ python3 -m textkit sentence_count "Dr. Smith arrived. Was it late? Yes!"
3
```
