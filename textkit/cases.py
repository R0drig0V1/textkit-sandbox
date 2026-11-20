"""Identifier case conversions. Every public function is listed in the README's function table.

How an identifier is split into words (separators, runs of capitals, digits) is decided in
docs/decisions/0001-to-snake-case-word-boundaries.md; its table of cases is tested row by row
in tests/test_cases.py.
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
