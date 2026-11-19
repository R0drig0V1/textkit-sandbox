"""Identifier case conversions (snake_case, camelCase, kebab-case).

How an identifier is split into words, runs of capitals and digits included, is decided in
docs/decisions/0002-splitting-runs-of-capitals.md; its table of cases is tested row by row in
tests/test_cases.py. Every public function is listed in the README's function table.
"""

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
    return "_".join(word.lower() for word in _split_identifier(name))
