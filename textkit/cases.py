"""Identifier case conversions (snake_case, camelCase, ...).

Every public function is listed in the README's function table. How words are found inside
an identifier, runs of capitals included, is decided in the ADR "How `to_snake_case`
splits runs of capitals" (docs/decisions/NNNN-snake-case-capital-runs.md).
"""

import re

# `_` and `-` separate words; a run of them counts as one separator.
_SEPARATORS = re.compile(r"[-_]+")


def _split_capital_runs(chunk: str) -> list[str]:
    """Split a separator-free chunk into words at case boundaries (see the module docstring's ADR).

    A word starts at an upper-case character that follows a lower-case character or a digit
    (``camelCase``, ``HTTP2Server``), or that ends a run of capitals because the next
    character is lower-case (``HTTPServer`` -> ``HTTP`` + ``Server``). Digits never start a
    word: they stay with the word before them (``parseURL2`` -> ``parse`` + ``URL2``).
    """
    words = []
    start = 0
    for i in range(1, len(chunk)):
        char, prev = chunk[i], chunk[i - 1]
        if not char.isupper():
            continue
        nxt = chunk[i + 1] if i + 1 < len(chunk) else ""
        if prev.islower() or prev.isdigit() or (prev.isupper() and nxt.islower()):
            words.append(chunk[start:i])
            start = i
    words.append(chunk[start:])
    return words


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    ``_`` and ``-`` are separators: a run of them becomes one ``_`` and separators at either
    end are dropped (``"-a--b-"`` -> ``"a_b"``). Inside each separator-free chunk, words are
    split at case boundaries; a run of capitals is one word, except that its last capital
    starts the next word when a lower-case letter follows it (``"HTTPServer"`` ->
    ``"http_server"``), and digits stay with the word before them (``"parseURL2"`` ->
    ``"parse_url2"``). Every word is lower-cased. Input that is already snake_case comes back
    unchanged, and ``""`` (or separators only) gives ``""``. Other characters (spaces,
    punctuation) are neither separators nor boundaries: they are kept, lower-cased.
    Upper/lower case follows ``str.isupper``/``str.islower``, so non-ASCII letters split too.
    The full rule and its table of cases are in the ADR "How `to_snake_case` splits
    runs of capitals" (docs/decisions/NNNN-snake-case-capital-runs.md).

    Raises ``TypeError`` if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    words = []
    for chunk in _SEPARATORS.split(name):
        if chunk:  # empty chunks come from separators at either end
            words.extend(_split_capital_runs(chunk))
    return "_".join(word.lower() for word in words)


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    ``_`` and ``-`` are separators: a run of them counts as one and separators at either end
    are dropped (``"__a--b_"`` -> ``"aB"``). The first word is lower-cased and every other word
    is capitalized with ``str.capitalize`` (first character upper-cased, the rest
    lower-cased), so ``"HTTP_server"`` -> ``"httpServer"`` and ``"user_ID"`` -> ``"userId"``.
    Unlike ``to_snake_case``, words are found only at separators, never at case boundaries:
    input with no separator at all is returned with only its first character lower-cased
    (``"PascalCase"`` -> ``"pascalCase"``, ``"HTTPServer"`` -> ``"hTTPServer"``), so
    camelCase input comes back unchanged. A single word between separators is lower-cased
    like any first word (``"_PascalCase"`` -> ``"pascalcase"``). ``""`` (or separators only)
    gives ``""``. Other characters (spaces, punctuation) are neither separators nor
    boundaries and are kept as they are, apart from the case changes above.

    Raises ``TypeError`` if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    if not _SEPARATORS.search(name):
        # No separator means the caller already has an identifier in some cased form; the
        # plan asks to keep it as is except for the first character, not to re-split it.
        return name[:1].lower() + name[1:]
    words = [word for word in _SEPARATORS.split(name) if word]  # ends give empty chunks
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])
