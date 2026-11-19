"""Identifier case conversions (snake_case, camelCase and friends).

Every public function is listed in the README's function table. How words are split out of
an identifier, runs of capitals included, is decided in ADR 0001
(docs/decisions/0001-to-snake-case-capital-runs.md); `to_camel_case` uses its separator rule.
`to_snake_case` takes its chunks from `textkit._tokens.words` (ADR 0002) when the two ADRs
split the name the same way (see `_chunks`).
"""

import re

from textkit._tokens import words

# `_` and `-` separate words; a run of them counts as one separator (ADR 0001).
_SEPARATORS = re.compile(r"[-_]+")


def _split_camel(chunk: str) -> list[str]:
    """Split one separator-free chunk of an identifier at its case boundaries.

    A word starts at an upper-case character that follows a lower-case character or a digit
    (`camelCase`, `utf8Encode`), or that ends a run of capitals and is followed by a
    lower-case character (`HTTPServer` -> `HTTP`, `Server`). Digits never start a word: they
    stay with what comes before them (`parseURL2` -> `parse`, `URL2`).
    """
    parts: list[str] = []
    start = 0
    for i in range(1, len(chunk)):
        char, prev = chunk[i], chunk[i - 1]
        if not char.isupper():
            continue
        after_lower = prev.islower() or prev.isdigit()
        # Last capital of a run, followed by lower case: it starts the next word.
        ends_run = prev.isupper() and i + 1 < len(chunk) and chunk[i + 1].islower()
        if after_lower or ends_run:
            parts.append(chunk[start:i])
            start = i
    parts.append(chunk[start:])
    return parts


def _chunks(name: str) -> list[str]:
    """Cut ``name`` into separator-free chunks at `_` and `-` (ADR 0001, rule 1).

    Empty chunks may appear and are dropped by the caller. When ``name`` holds only
    alphanumerics and `_`, the word rule of ADR 0002 (`textkit._tokens.words`) cuts it exactly
    as ADR 0001 does, so the shared tokenizer is used. Any other name keeps the
    separator split, because there the two rules disagree: a `-` between alphanumerics joins
    a word under ADR 0002 but separates under ADR 0001 (`kebab-case`), and characters that
    ADR 0002 drops as separators (spaces, `.`, `$`, a combining mark after `_`) are kept by
    ADR 0001.
    """
    if all(ch.isalnum() or ch == "_" for ch in name):
        return words(name)
    return _SEPARATORS.split(name)


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
    parts = [part for chunk in _chunks(name) for part in _split_camel(chunk) if part]
    return "_".join(part.lower() for part in parts)


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    The name is cut into words at `_` and `-` (a run of them counts as one, ADR 0001), and
    separators at either end are dropped. The first word is lower-cased and every other word
    capitalized with `str.capitalize`, so the rest of each word is lower-cased too
    (`"user_id"` -> `"userId"`, `"HTTP_server"` -> `"httpServer"`). A name with no separator
    at all is not split: only its first character is lower-cased (`"PascalCase"` ->
    `"pascalCase"`, `"userId"` -> `"userId"`), so camelCase input comes back unchanged. Other
    characters, spaces and digits included, are not separators and are kept. A name made only
    of separators gives `""`.

    Raises:
        TypeError: if `name` is not a `str`.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    if not _SEPARATORS.search(name):
        # No separator: the name may already be camelCase or PascalCase, whose inner
        # capitals carry the word boundaries, so only the first character changes.
        return name[:1].lower() + name[1:]
    words = [word for word in _SEPARATORS.split(name) if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase or snake_case identifier to kebab-case.

    Built on `to_snake_case`, so words are split exactly as ADR 0001 says: at `_` and `-` (a
    run of them counts as one, leading and trailing ones dropped) and at case boundaries, a run
    of capitals staying one word (`"HTTPServer"` -> `"http-server"`) and digits staying with
    the word before them (`"parseURL2"` -> `"parse-url2"`). The words are lower-cased and
    joined with `-`; kebab-case input comes back unchanged. Other characters, spaces included,
    are not separators and are kept (lower-cased).

    Raises:
        TypeError: if `name` is not a `str`.
    """
    # `to_snake_case` consumes every `_` and `-` of the input as a separator, so each `_` in
    # its result is a word boundary and nothing else: swapping them is the whole conversion.
    return to_snake_case(name).replace("_", "-")
