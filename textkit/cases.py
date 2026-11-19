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
# Runs of separators count as one; T1.8 (`to_camel_case`) uses the same separators.
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
