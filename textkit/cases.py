"""Identifier case conversions (snake_case and friends).

Every public function is listed in the README's function table. How words are split out of
an identifier, runs of capitals included, is decided in ADR 0001
(docs/decisions/0001-to-snake-case-capital-runs.md).
"""

import re

# `_` and `-` separate words; a run of them counts as one separator (ADR 0001).
_SEPARATORS = re.compile(r"[-_]+")


def _split_camel(chunk: str) -> list[str]:
    """Split one separator-free chunk of an identifier at its case boundaries.

    A word starts at an upper-case character that follows a lower-case character or a digit
    (`camelCase`, `utf8Encode`), or that ends a run of capitals and is followed by a
    lower-case character (`HTTPServer` -> `HTTP`, `Server`). Digits never start a word: they
    stay with what comes before them (`parseURL2` -> `parse`, `URL2`).
    """
    words: list[str] = []
    start = 0
    for i in range(1, len(chunk)):
        char, prev = chunk[i], chunk[i - 1]
        if not char.isupper():
            continue
        after_lower = prev.islower() or prev.isdigit()
        # Last capital of a run, followed by lower case: it starts the next word.
        ends_run = prev.isupper() and i + 1 < len(chunk) and chunk[i + 1].islower()
        if after_lower or ends_run:
            words.append(chunk[start:i])
            start = i
    words.append(chunk[start:])
    return words


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    The name is cut into words at `_` and `-` (a run of them counts as one) and at case
    boundaries; the words are lower-cased and joined with `_`. A run of capitals is one word,
    except that its last capital starts the next word when a lower-case character follows
    (`"HTTPServer"` -> `"http_server"`); digits stay with the word before them
    (`"parseURL2"` -> `"parse_url2"`). Leading and trailing separators are dropped
    (`"_private"` -> `"private"`), and snake_case input comes back unchanged. Other
    characters, spaces included, are not separators and are kept (lower-cased). See ADR 0001
    for the full rule and its table of cases.

    Raises:
        TypeError: if `name` is not a `str`.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    words = [word for chunk in _SEPARATORS.split(name) for word in _split_camel(chunk) if word]
    return "_".join(word.lower() for word in words)
