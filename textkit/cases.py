"""Identifier case conversion (snake_case, camelCase, kebab-case).

Every public function is listed in the README's function table. How words are split out of
an identifier, runs of capitals included, is decided in ADR 0001
(docs/decisions/0001-to-snake-case-word-boundaries.md).
"""

import re

# A run of capitals followed by a capitalized word: the last capital starts the new word
# ("HTTPServer" -> "HTTP" + "Server"). ASCII only, see ADR 0001.
_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A lower-case letter or digit followed by a capital starts a new word ("camelCase",
# "base64Encode"). Digits never start a word on their own, so "parseURL2" keeps "URL2".
_LOWER_UPPER_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
# Runs of separators count as one; shared by `to_snake_case` and `to_camel_case` (ADR 0001, rule 4).
_SEPARATORS = re.compile(r"[-_]+")


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
    split = _ACRONYM_BOUNDARY.sub(r"\1_\2", name)
    split = _LOWER_UPPER_BOUNDARY.sub(r"\1_\2", split)
    return _SEPARATORS.sub("_", split).strip("_").lower()


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
