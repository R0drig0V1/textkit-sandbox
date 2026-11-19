"""Identifier case conversion. Every public function is listed in the README's function table.

How `to_snake_case` splits words inside an identifier (runs of capitals, digits) is fixed by
docs/decisions/0001-snake-case-word-boundaries.md; its case table is tested row by row in
tests/test_cases.py. `to_camel_case` splits only at the `_` and `-` separators.
`to_snake_case` splits at `_` with the shared tokenizer
(`textkit._tokens.words`, the prose word rule of ADR 0002) only where both ADRs agree.
"""

import re

from textkit import _tokens

# Both patterns use explicit ASCII ranges on purpose: non-ASCII letters never create a word
# boundary (ADR 0001), and `[A-Z]` in a str pattern does not match them.

# The last capital of a run starts a new word when a lower-case letter follows it:
# "HTTPServer" -> "HTTP_Server".
_ACRONYM_THEN_WORD = re.compile(r"([A-Z])([A-Z][a-z])")
# A capital after a lower-case letter or a digit starts a new word:
# "camelCase" -> "camel_Case", "HTTP2Server" -> "HTTP2_Server".
_LOWER_OR_DIGIT_THEN_UPPER = re.compile(r"([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    Every ``-`` becomes ``_``; existing underscores are kept as they are, so snake_case input
    only gets lower-cased. A new ``_`` is inserted before a capital that follows a lower-case
    letter or a digit (``camelCase`` -> ``camel_case``) and before the last capital of a run
    when a lower-case letter follows it (``HTTPServer`` -> ``http_server``). Digits stay with
    the word before them (``parseURL2`` -> ``parse_url2``). The result is lower-cased.

    Only ASCII letters create word boundaries; any other character passes through, lower-cased
    by ``str.lower``. The rule and its known limits (plural acronyms such as ``URLs``) are in
    ADR 0001. ``""`` gives ``""``. Never raises for a ``str`` argument.
    """
    text = name.replace("-", "_")
    # ADR 0001 and ADR 0002 split the same way at a single `_` between two words, and only
    # there: ADR 0002 never splits camelCase, and it drops what ADR 0001 keeps (leading,
    # trailing or doubled `_`, spaces, other punctuation). So the shared tokenizer splits the
    # identifier only when it is exactly its words joined by single `_`; anything else is
    # handled whole, as before. The substitutions below never match across `_`, so both paths
    # give the same result.
    parts = _tokens.words(text)
    if "_".join(parts) != text:
        parts = [text]
    # Acronym boundary first: it only looks at capitals, so the second pass cannot undo it.
    parts = [_ACRONYM_THEN_WORD.sub(r"\1_\2", part) for part in parts]
    parts = [_LOWER_OR_DIGIT_THEN_UPPER.sub(r"\1_\2", part) for part in parts]
    return "_".join(parts).lower()


# A run of separators counts as one; empty pieces from leading or trailing runs are dropped.
_SEPARATORS = re.compile(r"[_-]+")


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    The separators are ``_`` and ``-``; a run of them counts as one, and leading or trailing
    separators are dropped. The first word is lower-cased with ``str.lower`` and every other
    word is capitalized with ``str.capitalize`` (first character upper-cased, the rest
    lower-cased): ``"user_id"`` -> ``"userId"``, ``"HTTP_server"`` -> ``"httpServer"``,
    ``"user_HTTP"`` -> ``"userHttp"``.

    Input with no separator at all is returned with only its first character lower-cased, so
    camelCase passes through and PascalCase becomes camelCase (``"UserId"`` -> ``"userId"``).
    Input made only of separators gives ``""``, and so does ``""``.

    This function does not split at capitals: it is not the inverse of ``to_snake_case``,
    whose word boundaries are fixed by ADR 0001. Never raises for a ``str`` argument.
    """
    if "_" not in name and "-" not in name:
        return name[:1].lower() + name[1:]
    # Leading and trailing runs produce empty pieces at the ends; dropping them drops those
    # separators.
    words = [word for word in _SEPARATORS.split(name) if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase or snake_case identifier to kebab-case.

    Built on :func:`to_snake_case`: the words are split by the rule of ADR 0001 (acronyms,
    digits, ASCII-only boundaries), lower-cased, and every ``_`` of the result becomes ``-``
    (``HTTPServer`` -> ``http-server``, ``parseURL2`` -> ``parse-url2``).

    Underscores already in the input are treated like hyphens: each one becomes exactly one
    ``-``, with no collapsing or stripping, so ``snake_case`` -> ``snake-case``,
    ``a__b`` -> ``a--b`` and ``_private`` -> ``-private``. kebab-case input is only
    lower-cased. The limits of ADR 0001 carry over (``parseURLs`` -> ``parse-ur-ls``).
    ``""`` gives ``""``. Never raises for a ``str`` argument.
    """
    # Reusing to_snake_case keeps a single word-boundary rule (ADR 0001) for every case style.
    return to_snake_case(name).replace("_", "-")
