<!-- Usage guide: one runnable example per public function (plan task T2.8). Every ">>>" line
is executed by tests/test_usage.py through doctest, so scripts/check.sh fails if an example
goes stale. Keep a blank line before each closing fence: doctest reads expected output up to
the first blank line, so a fence right after the output would be taken as part of it. -->
# Using textkit

`textkit` is a small package of text helpers (standard library only, Python 3.9+). This page
shows one short example for each public function, grouped by module. The examples are
doctests: `tests/test_usage.py` runs every one of them, and checks that every public function
is called here at least once, so a new function needs an example on this page.

The full list of functions is the table in the [README](../README.md#functions); the rules
behind the less obvious choices are in [docs/decisions/](decisions/README.md).

## Strings: `textkit.strings`

`slugify` turns text into a lower-case ASCII slug. Non-ASCII characters are removed, not
transliterated, so strip accents first when you want to keep the letters.

```pycon
>>> from textkit.strings import slugify
>>> slugify("Hello, World!")
'hello-world'

```

`slug_title` is a slug cut to a maximum length that never ends in `-`.

```pycon
>>> from textkit.strings import slug_title
>>> slug_title("Hello, World!", 8)
'hello-wo'
>>> slug_title("Hello, World!", 6)
'hello'

```

`truncate` keeps the start of the text and marks the cut with a suffix (`"..."` by default);
the result, suffix included, is exactly `width` long. A width shorter than the suffix is an
error, `InvalidValueError` (see [Errors](#errors-textkiterrors)).

```pycon
>>> from textkit.strings import truncate
>>> truncate("Hello, World!", 8)
'Hello...'
>>> truncate("Hello", 8)
'Hello'
>>> truncate("Hello", 2)
Traceback (most recent call last):
    ...
textkit.errors.InvalidValueError: width (2) must be at least the suffix length (3)

```

`strip_accents` removes combining marks; letters with no decomposition, such as `ø`, stay.

```pycon
>>> from textkit.strings import strip_accents
>>> strip_accents("Ñandú")
'Nandu'

```

`squeeze` collapses every run of whitespace into one space and strips both ends.

```pycon
>>> from textkit.strings import squeeze
>>> squeeze("  too   many\n\tspaces ")
'too many spaces'

```

`wrap` splits text into lines of at most `width` characters at spaces. Existing newlines are
treated as spaces, so the text is reflowed (ADR 0003).

```pycon
>>> from textkit.strings import wrap
>>> wrap("the quick brown fox jumps", 10)
['the quick', 'brown fox', 'jumps']

```

`is_palindrome` ignores case, accents, spaces and punctuation.

```pycon
>>> from textkit.strings import is_palindrome
>>> is_palindrome("Dábale arroz a la zorra el abad")
True
>>> is_palindrome("textkit")
False

```

## Counts: `textkit.counts`

`word_count` counts words by the rule of ADR 0002: hyphenated words, contractions and numbers
count once.

```pycon
>>> from textkit.counts import word_count
>>> word_count("A well-known fact: don't pay 3.14 twice.")
7

```

`char_freq` counts each non-whitespace character, case-sensitive, in order of first
occurrence.

```pycon
>>> from textkit.counts import char_freq
>>> char_freq("Hello hi")
{'H': 1, 'e': 1, 'l': 2, 'o': 1, 'h': 1, 'i': 1}

```

`reading_time` gives whole minutes at `wpm` words per minute (default 200), rounded up: any
text with a word takes at least one minute (ADR 0004).

```pycon
>>> from textkit.counts import reading_time
>>> reading_time("just a few words")
1
>>> reading_time("word " * 450)
3
>>> reading_time("")
0

```

`sentence_count` counts sentences; listed abbreviations such as `Dr.` and `e.g.`, initials,
and an end followed by a lower-case letter do not end one (ADR 0005).

```pycon
>>> from textkit.counts import sentence_count
>>> sentence_count("Dr. Smith arrived. He sat down... then left!")
2

```

`ngrams` gives the runs of `n` consecutive words (default 2), each word exactly as written
(ADR 0002); fewer than `n` words give `[]`.

```pycon
>>> from textkit.counts import ngrams
>>> ngrams("Don't stop me now")
[("Don't", 'stop'), ('stop', 'me'), ('me', 'now')]
>>> ngrams("one two three", 3)
[('one', 'two', 'three')]
>>> ngrams("alone", 2)
[]

```

## Identifier cases: `textkit.cases`

`to_snake_case` splits at separators and capitals; a run of capitals stays one word and digits
stay with the word before them (ADR 0001).

```pycon
>>> from textkit.cases import to_snake_case
>>> to_snake_case("HTTPServer")
'http_server'
>>> to_snake_case("parseURL2")
'parse_url2'

```

`to_kebab_case` splits exactly like `to_snake_case` and joins with `-`.

```pycon
>>> from textkit.cases import to_kebab_case
>>> to_kebab_case("userId")
'user-id'

```

`to_camel_case` splits only at `_` and `-`, so it is not the inverse of `to_snake_case`.

```pycon
>>> from textkit.cases import to_camel_case
>>> to_camel_case("user_id")
'userId'
>>> to_camel_case("HTTP_server")
'httpServer'

```

## Diff: `textkit.diff`

`unified_diff` compares two texts line by line and returns the unified format of GNU
`diff -u` (`""` when they are equal). A line ends after each `"\n"`, so a `"\r"` is part
of its line, and a text without a final newline gets the `\ No newline at end of file`
marker. The format, the numbering and the tie rule are in [docs/diff.md](diff.md).

```pycon
>>> from textkit.diff import unified_diff
>>> print(unified_diff("one\ntwo\nthree\n", "one\n2\nthree\n"), end="")
--- a
+++ b
@@ -1,3 +1,3 @@
 one
-two
+2
 three
>>> print(unified_diff("a\n", "a\nb\n", context=0), end="")
--- a
+++ b
@@ -1,0 +2 @@
+b
>>> unified_diff("same\n", "same\n")
''

```

`apply_patch` applies such a diff, exactly at the lines its hunks state; a patch that does
not apply raises `PatchError` (an `InvalidValueError`) with the hunk's header in the message.

```pycon
>>> from textkit.diff import PatchError, apply_patch
>>> patch = unified_diff("one\ntwo\n", "one\n2\n")
>>> apply_patch("one\ntwo\n", patch)
'one\n2\n'
>>> try:
...     apply_patch("one\nTWO\n", patch)
... except PatchError as exc:
...     print("@@ -1,2 +1,2 @@" in str(exc))
True

```

`diff_words` compares the words of two texts (the rule of `word_count`, ADR 0002), each
exactly as it appears; spaces and punctuation are not compared.

```pycon
>>> from textkit.diff import diff_words
>>> diff_words("The quick fox.", "The slow, quick dog")
[('=', 'The'), ('+', 'slow'), ('=', 'quick'), ('-', 'fox'), ('+', 'dog')]

```

The subcommand `diff` prints `unified_diff` of two files (exit 0 equal, 1 different, 2 for a
file that cannot be read):

```sh
python3 -m textkit diff old.txt new.txt
```

## Errors: `textkit.errors`

A function that rejects a value raises `InvalidValueError`, with a message that names the
argument and the rule; its base class `TextkitError` is the base of every error textkit
raises on purpose, the error classes of the tool packages included. Catch `TextkitError` to
handle any rejected input.

```pycon
>>> from textkit.errors import InvalidValueError, TextkitError
>>> from textkit.strings import wrap
>>> try:
...     wrap("some text", 0)
... except TextkitError as exc:
...     print(f"{type(exc).__name__}: {exc}")
InvalidValueError: width must be at least 1, got 0

```

`InvalidValueError` is not a `ValueError` (ADR 0006): `except ValueError` does not catch it,
and a `ValueError` that escapes textkit is a bug in textkit, never a rejected input. An
argument of the wrong type still raises `TypeError`.

```pycon
>>> issubclass(InvalidValueError, TextkitError)
True
>>> issubclass(InvalidValueError, ValueError)
False

```

The command line exits 1 with the message on stderr, and no traceback, when a function command
raises a `TextkitError`; any other exception keeps its traceback.

## Markdown: `textkit.markdown`

`to_html` converts a small, safe subset of Markdown to HTML: raw HTML is escaped and links
to schemes other than `http`, `https` and `mailto` point to `#`. Every block and inline is
in [docs/markdown.md](markdown.md); the reasons are in ADR 0007.

```pycon
>>> from textkit.markdown import to_html
>>> print(to_html("# Notes\n\nSome *text* and [a link](https://example.com)."), end="")
<h1>Notes</h1>
<p>Some <em>text</em> and <a href="https://example.com">a link</a>.</p>
>>> to_html("[x](javascript:alert)")
'<p><a href="#">x</a></p>\n'

```

From the shell, `python3 -m textkit markdown notes.md` writes the HTML of a UTF-8 file.

## Templates: `textkit.template`

`render` fills a template from a dict: `{{ name }}` prints a value, `{% if %}` and
`{% for %}` choose and repeat, and filters such as `slug` and `truncate:<width>` transform
what is printed. The syntax, every filter and every error are in
[template.md](template.md).

```pycon
>>> from textkit.template import render
>>> render("Hello, {{ user.name | upper }}!", {"user": {"name": "Ada"}})
'Hello, ADA!'
>>> render("{% for t in tags %}{{ loop.index }}.{{ t | slug }} {% endfor %}", {"tags": ["Big Data", "AI"]})
'1.big-data 2.ai '

```

A name missing from the context is an error where it is printed and false in an `if`
(ADR 0008). Errors carry the line and column of the offending tag:

```pycon
>>> from textkit.template import TemplateError
>>> render("{% if admin %}root{% else %}guest{% endif %}", {})
'guest'
>>> try:
...     render("Hi\n{{ nmae }}", {"name": "Ada"})
... except TemplateError as error:
...     print(error.line, error.column, error.message)
2 1 'nmae' is not defined

```

From the shell, `python3 -m textkit render <template-file> <json-file>` does the same with
files; it prints `line:column: message` and exits 1 on a template error.

## Command line

Every public function that takes one text argument is also a command, with the other
parameters at their defaults; see "Commands" in the [README](../README.md#commands).

```sh
python3 -m textkit slugify "Hello, World!"     # prints hello-world
python3 -m textkit --help                      # lists the commands and the tools
```

The command line is the package `textkit/cli/`: `main.py` holds the parser, `functions.py`
discovers the function commands and `registry.py` holds the tool subcommands. A tool (a
package such as `textkit/template/`) adds its subcommand as one more module,
`textkit/cli/<name>.py`, without editing any other file: the module registers a `Command`
when it is imported, and `python3 -m textkit` finds it with `pkgutil`.

```python
"""Tool subcommand: python3 -m textkit shout <file> (an illustration, not a real tool)."""

import argparse
import sys

from textkit.cli.registry import PROG, Command, register


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file")


def _run(args: argparse.Namespace) -> int:
    try:
        with open(args.file, encoding="utf-8", newline="") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"{PROG} shout: error: {args.file}: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(text.upper())
    return 0


register(Command("shout", "Print a file in upper case", configure=_configure, run=_run))
```

`--help` lists the tools under `tools:`, after the function commands. The subcommand name is
the module name, and a tool can never take the name of a function command or of another tool:
both raise `RuntimeError` on every run. `_main` returns `run`'s exit code as is and catches
no error for a tool, so `run` handles its own.
