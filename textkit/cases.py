"""Identifier case conversion. Every public function is listed in the README's function table.

The word-splitting rules (runs of capitals, digits, separators) are fixed by
docs/decisions/0002-snake-case-word-splitting.md; change that ADR before changing them here.
"""

import re

# Runs of `-` and `_` are one separator; empty chunks (leading, trailing) are dropped.
_SEPARATORS = re.compile(r"[-_]+")
# An acronym followed by a capitalized word: the acronym's last capital starts the next word
# ("HTTPServer" -> "HTTP", "Server").
_ACRONYM_THEN_WORD = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A lower-case letter or digit followed by a capital: the capital starts a new word
# ("parseURL" -> "parse", "URL"; "Version2Beta" -> "Version2", "Beta").
_LOWER_THEN_UPPER = re.compile(r"([a-z0-9])([A-Z])")


def _split_words(name: str) -> list[str]:
    """Split an identifier into words, keeping their original case (rules in ADR 0002)."""
    words = []
    for chunk in _SEPARATORS.split(name):
        if not chunk:
            continue
        # The acronym rule runs first so that "HTTPServer" is cut before "S", not after "P".
        chunk = _ACRONYM_THEN_WORD.sub(r"\1_\2", chunk)
        chunk = _LOWER_THEN_UPPER.sub(r"\1_\2", chunk)
        words.extend(chunk.split("_"))
    return words


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    Words are split at `-` and `_` (a run of them counts as one; leading and trailing
    separators are dropped), before a capital that follows a lower-case letter or a digit
    (``"camelCase"`` -> ``"camel_case"``), and before the last capital of a run of capitals
    that is followed by a lower-case letter (``"HTTPServer"`` -> ``"http_server"``). Digits
    never start a word: they stay with what precedes them (``"parseURL2"`` -> ``"parse_url2"``).
    The words are lower-cased and joined with ``_``, so snake_case input comes back unchanged.

    Only ASCII capitals mark word boundaries; other characters, spaces included, are kept as
    they are apart from lower-casing. Returns ``""`` for ``""`` or separators only. Never
    raises for ``str`` input. See docs/decisions/0002-snake-case-word-splitting.md.
    """
    return "_".join(_split_words(name)).lower()
