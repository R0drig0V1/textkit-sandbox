"""Identifier case conversion. Every public function is listed in the README's function table.

The word-splitting rules (runs of capitals, digits, separators) are fixed by
docs/decisions/0002-snake-case-word-splitting.md; change that ADR before changing them here.
to_camel_case shares only its separator rule (rule 1): it never splits at case changes.
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


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    Words are split only at `-` and `_`, with the separator rule of ADR 0002 (a run of them
    counts as one; leading and trailing separators are dropped). The first word is
    lower-cased and every other word is capitalized with ``str.capitalize`` (first character
    upper-cased, the rest lower-cased), then the words are joined with nothing between them:
    ``"user_id"`` -> ``"userId"``, ``"HTTP_server"`` -> ``"httpServer"``,
    ``"SCREAMING_SNAKE"`` -> ``"screamingSnake"``.

    Case changes inside a word are not boundaries here, unlike in ``to_snake_case``: a name
    with no `-` or `_` at all is returned with only its first character lower-cased
    (``"PascalCase"`` -> ``"pascalCase"``, ``"camelCase"`` unchanged, ``"HTTPServer"`` ->
    ``"hTTPServer"``), while a word after a separator loses its inner capitals
    (``"my_camelCase"`` -> ``"myCamelcase"``). The conversion is lossy (``"version_2"`` and
    ``"version-2"`` both give ``"version2"``), so ``to_snake_case(to_camel_case(x))`` is not
    always ``x``.

    Spaces and other characters are not separators and are kept. Returns ``""`` for ``""``
    or separators only. Never raises for ``str`` input.
    """
    if "_" not in name and "-" not in name:
        # The plan (T1.8) keeps separator-free input as written apart from its first
        # character, so already-camelCase names are a fixed point.
        return name[:1].lower() + name[1:]
    words = [word for word in _SEPARATORS.split(name) if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase or snake_case identifier to kebab-case.

    Built on ``to_snake_case``, so the words are exactly the ones ADR 0002 gives (runs of
    capitals, digits and separators): the words are lower-cased and joined with ``-``
    instead of ``_``. ``"HTTPServer"`` -> ``"http-server"``, ``"parseURL2"`` ->
    ``"parse-url2"``, ``"already_snake"`` -> ``"already-snake"``; kebab-case input comes back
    unchanged. Like ``to_snake_case`` it is lossy (``"HTTPServer"`` and ``"HttpServer"`` both
    give ``"http-server"``).

    Spaces and other characters are not separators and are kept, only lower-cased
    (``"hello world"`` -> ``"hello world"``). Returns ``""`` for ``""`` or separators only.
    Never raises for ``str`` input. See docs/decisions/0002-snake-case-word-splitting.md.
    """
    # Safe as a plain replace: `_` and `-` are separators in ADR 0002, so no word of the
    # snake_case form contains one and every `_` in it is a word boundary.
    return to_snake_case(name).replace("_", "-")
