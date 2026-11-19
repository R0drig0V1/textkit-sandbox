"""Identifier case conversions (snake_case, camelCase, kebab-case).

How an identifier is split into words, runs of capitals and digits included, is decided in
docs/decisions/0002-splitting-runs-of-capitals.md; its table of cases is tested row by row in
tests/test_cases.py. `to_camel_case` takes already-separated input, so it applies only that
ADR's separator rule (rule 1). Every public function is listed in the README's function table.
"""

import re

from textkit import _tokens

# Characters that separate words explicitly. A run of them counts as one separator.
_SEPARATORS = "_-"


def _split_identifier(name: str) -> list[str]:
    """Split ``name`` into words following ADR 0002; empty words are dropped.

    Explicit separators (``_`` and ``-``) end a word. Inside a separator-free chunk, a word
    boundary goes before an upper-case character that follows a lower-case character or a
    digit (``camelCase``, ``utf8Decode``), and before the last capital of a run when a
    lower-case character follows it (``HTTPServer`` -> ``HTTP`` + ``Server``). Digits never
    start a word, so they stay with what precedes them (``parseURL2`` -> ``parse`` +
    ``URL2``).
    """
    words: list[str] = []
    current: list[str] = []
    for i, char in enumerate(name):
        if char in _SEPARATORS:
            if current:
                words.append("".join(current))
                current = []
            continue
        if current and char.isupper():
            prev = current[-1]
            nxt = name[i + 1] if i + 1 < len(name) else ""
            # Lower/digit -> upper starts a word; inside a run of capitals, only the capital
            # that begins a capitalised word (followed by a lower-case letter) starts one.
            if prev.islower() or prev.isdigit() or (prev.isupper() and nxt.islower()):
                words.append("".join(current))
                current = []
        current.append(char)
    if current:
        words.append("".join(current))
    return words


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    The identifier is split into words as described in ADR 0002, then the words are
    lower-cased and joined with ``_``:

    - ``"camelCase"`` -> ``"camel_case"``, ``"PascalCase"`` -> ``"pascal_case"``,
      ``"kebab-case"`` -> ``"kebab_case"``, ``"already_snake"`` -> ``"already_snake"``.
    - A run of capitals is one word, except that its last capital starts the next word
      when a lower-case letter follows: ``"HTTPServer"`` -> ``"http_server"``.
    - Digits stay with the word before them: ``"parseURL2"`` -> ``"parse_url2"``.
    - ``_`` and ``-`` are separators; a run of them counts as one and leading or trailing
      ones are dropped (``"__init__"`` -> ``"init"``). Any other character, spaces included,
      is kept as part of its word.

    Case tests use ``str.isupper``/``str.islower``/``str.isdigit``, so non-ASCII letters
    are handled; no Unicode normalization is applied. ``""`` (or separators only) gives
    ``""``.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    # ADR 0001 (the shared tokenizer) and ADR 0002 rule 1 split the same way only on names
    # made of letters, digits and "_": both end a word at a run of "_" and drop leading and
    # trailing ones. They disagree on "-" (a joiner in 0001, a separator here) and on any
    # other character (a separator in 0001, part of the word here), so such names keep the
    # ADR 0002 splitter for separators too. Rules 2-4 (case and digits) are identifier
    # rules with no ADR 0001 counterpart and always run on each chunk.
    if all(char.isalnum() or char == "_" for char in name):
        chunks = _tokens.words(name)
    else:
        chunks = [name]
    return "_".join(word.lower() for chunk in chunks for word in _split_identifier(chunk))


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    Only the explicit separators of ADR 0002 (rule 1) split words; rules 2-4 of that ADR
    (case changes and digits) are not applied, because the input is expected to be
    separated already:

    - ``_`` and ``-`` are separators; a run of them counts as one and leading or trailing
      ones are dropped: ``"user_id"`` -> ``"userId"``, ``"kebab-case"`` -> ``"kebabCase"``,
      ``"__init__"`` -> ``"init"``.
    - The first word is lower-cased and every other word is capitalized with
      ``str.capitalize`` (first character upper-case, the rest lower-case):
      ``"HTTP_server"`` -> ``"httpServer"``, ``"parse_URL2"`` -> ``"parseUrl2"``.
    - A name that contains no separator is returned with only its first character
      lower-cased, so camelCase input is unchanged and PascalCase becomes camelCase:
      ``"userId"`` -> ``"userId"``, ``"UserId"`` -> ``"userId"``. A name with a leading or
      trailing separator does contain one, so its words are case-folded as above
      (``"_userId"`` -> ``"userid"``).

    Any other character, spaces included, is kept as part of its word. ``""`` (or
    separators only) gives ``""``. The conversion is lossy, so
    ``to_camel_case(to_snake_case(x))`` does not always return ``x`` (ADR 0002,
    Consequences).

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    if not any(char in _SEPARATORS for char in name):
        # Already one word (or camel/PascalCase): keep its inner capitals.
        return name[:1].lower() + name[1:]
    words = [word for word in re.split(f"[{re.escape(_SEPARATORS)}]+", name) if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])
