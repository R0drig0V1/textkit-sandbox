"""Identifier case conversion. Every public function is listed in the README's function table.

The word-splitting rules for `to_snake_case` (separators, runs of capitals, digits) are
recorded in the ADR docs/decisions/NNNN-to-snake-case-capital-runs.md, which ends with the
table of cases that tests/test_cases.py checks row by row. `to_camel_case` goes the other
way (snake_case or kebab-case to camelCase); it splits on separators only.
"""

import re

# A run of `-` or `_` is one word boundary; splitting on it also drops leading and trailing
# separators (they produce empty parts, which are discarded).
_SEPARATORS = re.compile(r"[-_]+")
# Inside a run of capitals followed by a lower-case letter, the last capital starts the next
# word: "HTTPServer" -> "HTTP" + "Server". Greedy `[A-Z]+` backtracks by exactly one capital.
_ACRONYM_END = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A capital after a lower-case letter or a digit starts a new word: "camelCase", "utf8Encode".
# Digits never start a word themselves, so they stay with the word before them.
_LOWER_OR_DIGIT_THEN_UPPER = re.compile(r"([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    Words are split at runs of ``-`` or ``_`` (leading and trailing ones are dropped), before
    a capital that follows a lower-case ASCII letter or a digit, and before the last capital
    of a run of capitals that is followed by a lower-case letter. Digits stick to the word
    before them. The words are lower-cased and joined with single ``_``:
    ``"HTTPServer"`` -> ``"http_server"``, ``"parseURL2"`` -> ``"parse_url2"``,
    ``"kebab-case"`` -> ``"kebab_case"``. Already snake_case input is returned unchanged and
    ``""`` (or separators only) gives ``""``; the result is never changed by a second call.

    Boundaries are detected on ASCII letters and digits only; any other character (spaces,
    punctuation, non-ASCII letters) is kept in place, lower-cased by ``str.lower``, and never
    splits a word. The ADR ``*-to-snake-case-capital-runs.md`` in ``docs/decisions/`` has the
    full rule and its table of cases.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"to_snake_case() expects a str, got {type(name).__name__}")
    words: list[str] = []
    for part in _SEPARATORS.split(name):
        if not part:
            continue
        # `part` has no `_` left (it was a separator), so `_` can mark the inner boundaries.
        part = _ACRONYM_END.sub(r"\1_\2", part)
        part = _LOWER_OR_DIGIT_THEN_UPPER.sub(r"\1_\2", part)
        words.extend(part.split("_"))
    return "_".join(words).lower()


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    ``name`` is split at runs of ``_`` and/or ``-`` (a run counts as one separator; leading
    and trailing ones are dropped). The first word is lower-cased and every other word is
    capitalized with ``str.capitalize`` (first character upper-cased, the rest lower-cased),
    then the words are joined: ``"user_id"`` -> ``"userId"``, ``"HTTP_server"`` ->
    ``"httpServer"``, ``"kebab--case"`` -> ``"kebabCase"``. Separators only, or ``""``, give
    ``""``.

    Input with no separator at all is returned with only its first character lower-cased
    (``"UserId"`` -> ``"userId"``, ``"HTTPServer"`` -> ``"hTTPServer"``), so camelCase input
    is unchanged. Input that has a separator, even only a leading or trailing one, goes
    through the word rule instead: ``"_UserId"`` -> ``"userid"``.

    Capitals are not split, unlike ``to_snake_case`` (ADR
    ``*-to-snake-case-capital-runs.md``); that conversion loses the original capitals, so
    ``to_camel_case(to_snake_case(x))`` gives back ``x`` only for plain camelCase ``x``.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"to_camel_case() expects a str, got {type(name).__name__}")
    if not _SEPARATORS.search(name):
        # No word boundaries to work with: keep the caller's capitals, lower only the first.
        return name[:1].lower() + name[1:]
    # Leading and trailing separators produce empty parts; runs never do, since the pattern
    # consumes the whole run.
    words = [part for part in _SEPARATORS.split(name) if part]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])
