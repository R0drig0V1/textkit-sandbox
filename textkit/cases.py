"""Identifier case conversions. Every public function is listed in the README's function table.

How ``to_snake_case`` splits an identifier into words (separators, runs of capitals, digits)
is decided in docs/decisions/0001-to-snake-case-word-boundaries.md; its table of cases is
tested row by row in tests/test_cases.py. ``to_camel_case`` splits only at ``_`` and ``-``
(plan task T1.8), so the two are not inverses of each other. ``to_kebab_case`` is
``to_snake_case`` with ``-`` as the separator, so it follows ADR 0001 exactly.
"""


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    The name is split into words, which are lower-cased and joined with ``_``:

    - every run of characters that are not alphanumeric (``-``, ``_``, spaces, ...) separates
      words, and separators at either end are dropped (``"--a--b--"`` -> ``"a_b"``);
    - an upper-case letter starts a new word when the previous character is not upper-case
      (``"camelCase"`` -> ``"camel_case"``, ``"URL2Path"`` -> ``"url2_path"``);
    - in a run of capitals, the last one starts a new word when a lower-case letter follows
      it (``"HTTPServer"`` -> ``"http_server"``);
    - digits never start a word; they stay with the word before them
      (``"parseURL2"`` -> ``"parse_url2"``).

    Snake_case input comes back lower-cased and otherwise unchanged; ``""`` gives ``""``.
    Letters are classified with ``str.isupper``/``str.islower``, so non-ASCII letters work too.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    return "_".join(word.lower() for word in _split_words(name))


def _split_words(name: str) -> list[str]:
    """Split ``name`` into words by the rules of ``to_snake_case`` (case is preserved)."""
    words: list[str] = []
    start = None  # index where the current word began, or None between words
    for i, char in enumerate(name):
        if not char.isalnum():
            if start is not None:
                words.append(name[start:i])
                start = None
            continue
        if start is None:
            start = i
        elif char.isupper() and _starts_word(name, i):
            words.append(name[start:i])
            start = i
    if start is not None:
        words.append(name[start:])
    return words


def _starts_word(name: str, i: int) -> bool:
    """Whether the upper-case letter at ``name[i]``, inside a word, starts a new one.

    ``name[i - 1]`` is known to be alphanumeric. Inside a run of capitals only the letter
    followed by a lower-case one starts a word: that is how "HTTPServer" keeps "HTTP" whole.
    """
    if not name[i - 1].isupper():
        return True
    return i + 1 < len(name) and name[i + 1].islower()


def to_camel_case(name: str) -> str:
    """Convert a snake_case or kebab-case identifier to camelCase.

    The name is split at ``_`` and ``-`` only; a run of them counts as one separator, and
    separators at either end are dropped (``"__user--id__"`` -> ``"userId"``). The first word
    is lower-cased and every other word capitalized with ``str.capitalize``, so the rest of
    each word is lower-cased too (``"HTTP_server"`` -> ``"httpServer"``,
    ``"user_ID"`` -> ``"userId"``). Other characters, spaces and dots included, are not
    separators and are kept as they are.

    Input with no ``_`` or ``-`` is returned with only its first character lower-cased
    (``"UserId"`` -> ``"userId"``, ``"HTTPServer"`` -> ``"hTTPServer"``): without a separator
    there are no word boundaries to rebuild, and this function, unlike ``to_snake_case``,
    does not guess them from capitals. ``""`` and separator-only input give ``""``.

    This is not the inverse of ``to_snake_case`` (see ADR 0001): ``"HTTPServer"`` ->
    ``"http_server"`` -> ``"httpServer"``.

    Raises:
        TypeError: if ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a str, not {type(name).__name__}")
    if "_" not in name and "-" not in name:
        return name[:1].lower() + name[1:]
    # Splitting on one separator kind after mapping the other to it leaves empty strings for
    # runs and for leading/trailing separators; dropping them gives "a run counts as one".
    words = [word for word in name.replace("-", "_").split("_") if word]
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase or snake_case identifier to kebab-case.

    Built on ``to_snake_case``: the name is split into words by exactly the same rules
    (ADR 0001: runs of capitals, digits, separators), and the words are lower-cased and
    joined with ``-`` instead of ``_`` (``"HTTPServer"`` -> ``"http-server"``,
    ``"parseURL2"`` -> ``"parse-url2"``, ``"user_id"`` -> ``"user-id"``). Kebab-case input
    comes back lower-cased and otherwise unchanged; ``""`` and separator-only input give ``""``.

    The same limitations as ``to_snake_case`` apply (``"PDFs"`` -> ``"pd-fs"``).

    Raises:
        TypeError: if ``name`` is not a ``str`` (raised by ``to_snake_case``).
    """
    # Safe to replace every "_": to_snake_case joins words made only of alphanumeric
    # characters, so each "_" in its output is a separator, never part of a word.
    return to_snake_case(name).replace("_", "-")
