"""Identifier case conversion. Every public function is listed in the README's function table.

How word boundaries are found inside an identifier (runs of capitals, digits, separators) is
decided in docs/decisions/0002-snake-case-capital-runs.md.
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
