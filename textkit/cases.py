"""Identifier case conversion helpers. Every public function is listed in the README's table.

The word-boundary rules are recorded in docs/decisions/0001-snake-case-capital-runs.md.
"""

import re

# A run of capitals followed by a capitalized word: the last capital starts the new word
# ("HTTPServer" -> "HTTP" + "Server"), so acronyms stay whole.
_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A lower-case letter or digit followed by a capital starts a new word ("parseURL" ->
# "parse" + "URL", "url2Parser" -> "url2" + "Parser"). Digits never start a word themselves.
_LOWER_UPPER_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
# Any run of separators ("-", "_", or a mix) becomes a single "_".
_SEPARATORS = re.compile(r"[-_]+")


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    Word boundaries are placed before a capital that follows a lower-case ASCII letter or a
    digit, and before the last capital of a run of capitals when a lower-case letter follows
    it, so acronyms stay whole: ``"HTTPServer"`` -> ``"http_server"``, ``"parseURL2"`` ->
    ``"parse_url2"``. Digits stay attached to the word before them. ``-`` and ``_`` are
    separators: a run of them becomes one ``_`` and separators at either end are dropped.
    The result is lower-cased with ``str.lower``.

    Input that is already snake_case is returned unchanged, and ``""`` gives ``""``. Never
    raises for a ``str``; other characters (spaces, punctuation, non-ASCII letters) are not
    treated as boundaries and are kept as they are, apart from lower-casing.
    """
    text = _ACRONYM_BOUNDARY.sub(r"\1_\2", name)
    text = _LOWER_UPPER_BOUNDARY.sub(r"\1_\2", text)
    text = _SEPARATORS.sub("_", text).strip("_")
    return text.lower()
