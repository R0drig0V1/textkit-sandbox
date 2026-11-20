"""Identifier case conversion. Every public function is listed in the README's function table.

How a name is split into words (separators, runs of capitals, digits) is fixed by
docs/decisions/0001-to-snake-case-word-boundaries.md; later converters build on it.
"""

import re

# `_` and `-` separate words; a run of them counts as one separator (ADR 0001, rule 1).
_SEPARATORS = re.compile(r"[-_]+")


def _split_chunk(chunk: str) -> list[str]:
    """Split a separator-free chunk into words at case boundaries (ADR 0001, rules 2-4).

    A word starts at an upper-case character that follows a lower-case character or a
    digit (`camelCase`, `utf8Decoder`), or that follows another upper-case character and
    precedes a lower-case one, so the last capital of a run starts the next word
    (`HTTPServer` -> `HTTP`, `Server`). Digits never start a word on their own.
    """
    words = []
    start = 0
    for i in range(1, len(chunk)):
        prev, cur = chunk[i - 1], chunk[i]
        nxt = chunk[i + 1] if i + 1 < len(chunk) else ""
        if cur.isupper() and (
            prev.islower() or prev.isdigit() or (prev.isupper() and nxt.islower())
        ):
            words.append(chunk[start:i])
            start = i
    words.append(chunk[start:])
    return words


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case name to snake_case.

    The name is cut into words at every run of `_` or `-` (leading and trailing ones are
    dropped) and at case boundaries; a run of capitals is one word, except that its last
    capital starts the next word when a lower-case letter follows (`"HTTPServer"` ->
    `"http_server"`). Digits stay with the word before them (`"parseURL2"` ->
    `"parse_url2"`). The words are lower-cased and joined with `_`, so snake_case input
    comes back unchanged. Upper/lower case is Unicode-aware (`str.isupper`,
    `str.islower`); any other character is kept and never starts a word.

    Never raises for a `str`; `""` and separator-only input give `""`. The full rule and
    its table of cases are in ADR 0001 (docs/decisions/).
    """
    words = []
    for chunk in _SEPARATORS.split(name):
        if chunk:
            words.extend(_split_chunk(chunk))
    return "_".join(word.lower() for word in words)
