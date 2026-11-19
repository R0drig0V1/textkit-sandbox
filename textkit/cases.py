"""Identifier case conversion. Every public function is listed in the README's function table.

How word boundaries are found inside an identifier (runs of capitals, digits, separators) is
decided in docs/decisions/0003-snake-case-capital-runs.md. ``to_camel_case`` splits only at
``-`` and ``_`` (plan task T1.8), so that ADR's capital-run rules do not apply to it.
"""

import re

# An acronym followed by a capitalised word ("HTTPServer"): the last capital of the run
# starts the next word, so the boundary goes before it.
_ACRONYM_THEN_WORD = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A lower-case letter or a digit followed by a capital ("camelCase", "parseURL", "v2Beta").
_LOWER_OR_DIGIT_THEN_UPPER = re.compile(r"([a-z0-9])([A-Z])")
# A run of separators counts as one boundary ("kebab--case", "snake__case", "mixed-_case").
_SEPARATORS = re.compile(r"[-_]+")


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase, kebab-case or snake_case identifier to snake_case.

    A new word starts at a capital that follows a lower-case letter or a digit
    (``"camelCase"`` -> ``"camel_case"``), and at the last capital of a run of capitals that
    is followed by a lower-case letter (``"HTTPServer"`` -> ``"http_server"``). Digits stay
    with the word before them (``"parseURL2"`` -> ``"parse_url2"``). Each run of ``-`` and
    ``_`` becomes one ``_``, and separators at either end are dropped. The result is
    lower-cased. ``""`` gives ``""``.

    Boundaries are detected for ASCII letters only; any other character is lower-cased and
    kept, but never starts a word. Never raises for a ``str`` argument.
    """
    spaced = _ACRONYM_THEN_WORD.sub(r"\1_\2", name)
    spaced = _LOWER_OR_DIGIT_THEN_UPPER.sub(r"\1_\2", spaced)
    return _SEPARATORS.sub("_", spaced).strip("_").lower()


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    ``-`` and ``_`` are separators, and a run of them counts as one (``"user__id"`` ->
    ``"userId"``). Separators at either end are dropped. The first word is lower-cased and
    every following word is capitalized with ``str.capitalize`` (first character upper-case,
    the rest lower-case): ``"user_id"`` -> ``"userId"``, ``"HTTP_server"`` -> ``"httpServer"``.

    Input with no separator is assumed to be a single word or already camelCase/PascalCase,
    so only its first character is lower-cased and the rest is kept as is
    (``"PascalCase"`` -> ``"pascalCase"``, ``"HTTPServer"`` -> ``"hTTPServer"``). Input made
    only of separators gives ``""``, and so does ``""``. Never raises for a ``str`` argument.
    """
    if not _SEPARATORS.search(name):
        # No word boundaries to work with: keep the caller's casing except the first letter.
        return name[:1].lower() + name[1:]
    words = [word for word in _SEPARATORS.split(name) if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase, snake_case or kebab-case identifier to kebab-case.

    Words are split exactly as in :func:`to_snake_case` (rules in
    docs/decisions/0003-snake-case-capital-runs.md) and joined with ``-`` instead of ``_``:
    ``"HTTPServer"`` -> ``"http-server"``, ``"parseURL2"`` -> ``"parse-url2"``,
    ``"SCREAMING_SNAKE"`` -> ``"screaming-snake"``. The result is lower-cased, and ``""``
    gives ``""``. Never raises for a ``str`` argument.
    """
    # Every "_" in to_snake_case's output is a word boundary (runs of separators are already
    # collapsed and the ends stripped), so swapping the joiner keeps the same words.
    return to_snake_case(name).replace("_", "-")
