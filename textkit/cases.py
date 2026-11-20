"""Identifier case conversion. Every public function is listed in the README's function table.

How a name is split into words (separators, runs of capitals, digits) is fixed by
docs/decisions/0001-to-snake-case-word-boundaries.md; later converters build on it.
"""

import re

from textkit._tokens import words

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
    # Rule 1 (separators) goes through the shared tokenizer (ADR 0002) only when the name
    # has nothing but letters, digits and `_`: there both rules cut at every run of `_` and
    # nowhere else. `-` and any other character keep the separator regex, because ADR 0002
    # joins a single `-` ("kebab-case" is one word) and splits on punctuation that ADR 0001
    # keeps inside a word. Case boundaries (rules 2-4) have no ADR 0002 counterpart, so
    # `_split_chunk` handles them on either path.
    if all(ch.isalnum() or ch == "_" for ch in name):
        chunks = words(name)
    else:
        chunks = [chunk for chunk in _SEPARATORS.split(name) if chunk]
    parts = []
    for chunk in chunks:
        parts.extend(_split_chunk(chunk))
    return "_".join(part.lower() for part in parts)


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case name to camelCase (`"user_id"` -> `"userId"`).

    `_` and `-` separate words; a run of them counts as one separator, and leading and
    trailing runs are dropped (the same separator rule as ADR 0001, rule 1). The first word
    is lower-cased and every other word capitalized with `str.capitalize` (first character
    upper-cased, the rest lower-cased), so `"HTTP_server"` -> `"httpServer"` and
    `"SCREAMING_SNAKE"` -> `"screamingSnake"`. Case boundaries inside a word are not split:
    that is `to_snake_case`'s job.

    A name with no separator at all is returned with only its first character lower-cased
    (`"PascalCase"` -> `"pascalCase"`), so camelCase input comes back unchanged.

    Never raises for a `str`; `""` and separator-only input give `""`. Lossy like
    `to_snake_case`: round trips between the two are not guaranteed (ADR 0001).
    """
    if not _SEPARATORS.search(name):
        # No separator: the plan keeps the name as typed apart from its first character,
        # so existing camelCase and PascalCase boundaries survive.
        return name[:1].lower() + name[1:]
    words = [chunk for chunk in _SEPARATORS.split(name) if chunk]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])
