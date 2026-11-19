"""Identifier case conversion (snake_case, camelCase, kebab-case).

Every public function is listed in the README's function table. How words are split out of
an identifier, runs of capitals included, is decided in ADR 0001
(docs/decisions/0001-to-snake-case-word-boundaries.md). Where that rule and the prose word
rule of ADR 0002 split the same way, `to_snake_case` splits with the shared tokenizer
`textkit._tokens.words` (plan task T1.10).
"""

import re

from textkit._tokens import words

# A run of capitals followed by a capitalized word: the last capital starts the new word
# ("HTTPServer" -> "HTTP" + "Server"). ASCII only, see ADR 0001.
_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A lower-case letter or digit followed by a capital starts a new word ("camelCase",
# "base64Encode"). Digits never start a word on their own, so "parseURL2" keeps "URL2".
_LOWER_UPPER_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
# Runs of separators count as one; shared by `to_snake_case` and `to_camel_case` (ADR 0001, rule 4).
_SEPARATORS = re.compile(r"[-_]+")


def _split_case(text: str) -> str:
    """Insert ``_`` at the case boundaries of ADR 0001, rules 1 to 3 (ASCII only)."""
    return _LOWER_UPPER_BOUNDARY.sub(r"\1_\2", _ACRONYM_BOUNDARY.sub(r"\1_\2", text))


def _splits_like_prose(name: str) -> bool:
    """Return True when ADR 0001 and ADR 0002 split ``name`` at exactly the same places.

    That is the case when every character is alphanumeric (``str.isalnum()``) or ``_``: both
    rules then cut at every run of ``_``, drop the ``_`` and keep each run of alphanumerics
    whole. Any other character makes them disagree: a single ``-`` joins in ADR 0002 but
    separates in ADR 0001 (``"kebab-case"``), and spaces, punctuation, symbols and combining
    marks are dropped as separators by ADR 0002 but kept in place by ADR 0001, rule 5.
    """
    return all(char.isalnum() or char == "_" for char in name)


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    Words are split at ``-`` and ``_`` (a run of them counts as one separator), before a
    capital that follows a lower-case letter or a digit (``"camelCase"`` -> ``"camel_case"``),
    and before the last capital of a run of capitals that is followed by a lower-case letter
    (``"HTTPServer"`` -> ``"http_server"``). Digits stay attached to the word before them
    (``"parseURL2"`` -> ``"parse_url2"``). The words are lower-cased and joined with ``_``;
    leading and trailing separators are dropped, so ``"__init__"`` gives ``"init"``. Input that
    is already snake_case is returned unchanged and ``""`` gives ``""``.

    Word boundaries are only detected between ASCII letters and digits; any other character
    (spaces, punctuation, non-ASCII letters) is kept in place and only lower-cased. The rules
    and the full table of cases are in ADR 0001.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    if _splits_like_prose(name):
        # The separators (rule 4) go through the shared tokenizer; the case boundaries
        # (rules 1 to 3) are specific to identifiers and still apply within each word. The
        # regexes only insert "_" between two ASCII alphanumerics, so applying them word by
        # word gives the same string as the fallback below.
        return "_".join(_split_case(word) for word in words(name)).lower()
    # Input with "-", spaces, punctuation or marks: ADR 0002 would split it differently, so
    # it keeps the identifier-only path (T1.10, see _splits_like_prose).
    return _SEPARATORS.sub("_", _split_case(name)).strip("_").lower()


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    ``name`` is split at ``-`` and ``_``; a run of them counts as one separator and separators
    at the start or end are dropped (``"__user__id__"`` -> ``"userId"``). The first word is
    lower-cased and every other word is capitalized with ``str.capitalize`` (first character
    upper-cased, the rest lower-cased), so ``"user_id"`` -> ``"userId"``, ``"HTTP_server"`` ->
    ``"httpServer"`` and ``"user_ID"`` -> ``"userId"``. Digits are kept as they are
    (``"utf_8"`` -> ``"utf8"``).

    Input with no separator is not split: it is returned with only its first character
    lower-cased, so ``"camelCase"`` stays ``"camelCase"``, ``"PascalCase"`` gives
    ``"pascalCase"`` and ``"HTTP"`` gives ``"hTTP"``. ``""`` and input made only of separators
    (``"__"``) give ``""``. Unlike ``to_snake_case``, no case boundaries are detected inside a
    word: ``"get_HTTPResponse"`` gives ``"getHttpresponse"``.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    if not _SEPARATORS.search(name):
        return name[:1].lower() + name[1:]
    # Leading, trailing and repeated separators produce empty parts; drop them.
    words = [word for word in _SEPARATORS.split(name) if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase or snake_case identifier to kebab-case.

    ``name`` is converted with ``to_snake_case`` and every ``_`` of the result is replaced by
    ``-``, so the word boundaries are exactly those of ADR 0001 (``"HTTPServer"`` ->
    ``"http-server"``, ``"parseURL2"`` -> ``"parse-url2"``, ``"already_snake"`` ->
    ``"already-snake"``). Runs of ``-`` and ``_`` count as one separator and separators at the
    start or end are dropped (``"__init__"`` -> ``"init"``); input that is already kebab-case
    is returned unchanged and ``""`` gives ``""``. Non-ASCII characters are kept in place and
    only lower-cased (``"Ñandú"`` -> ``"ñandú"``).

    Raises:
        TypeError: if ``name`` is not a ``str`` (raised by ``to_snake_case``).
    """
    # Every "_" in to_snake_case's output is a word separator (runs are already collapsed),
    # so a plain replace keeps ADR 0001's rules in one place.
    return to_snake_case(name).replace("_", "-")
