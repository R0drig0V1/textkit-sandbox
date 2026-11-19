"""Identifier case conversion helpers. Every public function is listed in the README's table.

The word-boundary rules of ``to_snake_case``, which ``to_kebab_case`` reuses, are recorded in
docs/decisions/0001-snake-case-capital-runs.md. ``to_camel_case`` splits only at separators
(plan task T1.8), so it does not apply those capital-run rules.
"""

import re

from textkit._tokens import words

# A run of capitals followed by a capitalized word: the last capital starts the new word
# ("HTTPServer" -> "HTTP" + "Server"), so acronyms stay whole.
_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
# A lower-case letter or digit followed by a capital starts a new word ("parseURL" ->
# "parse" + "URL", "url2Parser" -> "url2" + "Parser"). Digits never start a word themselves.
_LOWER_UPPER_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
# Any run of separators ("-", "_", or a mix) becomes a single "_".
_SEPARATORS = re.compile(r"[-_]+")
# Input where the word rule of 0002-what-counts-as-a-word (textkit._tokens.words) and the
# separator rule of 0001-snake-case-capital-runs split the same way: only ASCII letters,
# digits and "_". Both split at every run of "_" and drop it at the ends. They disagree on a
# single "-" (one word for words(), a separator here) and on other characters (dropped by
# words(), kept here), so input containing those keeps the regex path.
_SHARED_RULE_INPUT = re.compile(r"[A-Za-z0-9_]*")


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
    # The capital-run boundaries never involve "_", so splitting at "_" first and applying
    # them per word gives the same result as applying them to the whole name.
    parts = words(name) if _SHARED_RULE_INPUT.fullmatch(name) else [name]
    text = "_".join(
        _LOWER_UPPER_BOUNDARY.sub(r"\1_\2", _ACRONYM_BOUNDARY.sub(r"\1_\2", part))
        for part in parts
    )
    text = _SEPARATORS.sub("_", text).strip("_")
    return text.lower()


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase or snake_case identifier to kebab-case.

    Built on ``to_snake_case``, so it splits words by exactly the same rules
    (0001-snake-case-capital-runs):
    acronyms stay whole (``"HTTPServer"`` -> ``"http-server"``), digits stay attached to the
    word before them (``"parseURL2"`` -> ``"parse-url2"``), a run of ``-`` and ``_`` becomes
    one ``-``, separators at either end are dropped, and the result is lower-cased. Every
    ``_`` in the snake_case result is a word separator, so each one becomes a ``-``.

    Input that is already kebab-case is returned unchanged, and ``""`` gives ``""``. Never
    raises for a ``str``; other characters (spaces, punctuation, non-ASCII letters) are kept
    as they are, apart from lower-casing, as in ``to_snake_case``.
    """
    # to_snake_case already collapses every separator run to a single "_", so a plain
    # replace is enough; re-deriving the boundaries here would risk the two drifting apart.
    return to_snake_case(name).replace("_", "-")


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    ``-`` and ``_`` are separators; a run of them (``"a__b"``, ``"a-_b"``) counts as one and
    separators at either end are dropped. The first word is lower-cased with ``str.lower``
    and every following word is capitalized with ``str.capitalize`` (first character upper,
    the rest lower), so ``"user_id"`` -> ``"userId"`` and ``"HTTP_server"`` ->
    ``"httpServer"``. Capitals inside a word are not word boundaries.

    Input with no separator at all is returned with only its first character lower-cased
    (``"UserId"`` -> ``"userId"``, ``"HTTP"`` -> ``"hTTP"``), so camelCase input is left
    unchanged. ``""`` and separators only (``"__"``) give ``""``. Never raises for a ``str``;
    other characters (spaces, punctuation, digits, non-ASCII letters) are kept inside their
    word. Converting with ``to_snake_case`` and back is lossy for acronyms (ADR 0001).
    """
    if not _SEPARATORS.search(name):
        return name[:1].lower() + name[1:]
    # Splitting "-a__b-" gives empty strings at the ends: those are the dropped separators.
    words = [word for word in _SEPARATORS.split(name) if word]
    if not words:
        return ""
    first, *rest = words
    return first.lower() + "".join(word.capitalize() for word in rest)
