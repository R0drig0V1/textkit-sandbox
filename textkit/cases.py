"""Identifier case conversion helpers (snake_case and friends).

The word-boundary rules used here are recorded in
docs/decisions/0002-snake-case-word-boundaries.md; every example in that ADR is tested in
tests/test_cases.py. Every public function is listed in the README's function table.
"""

import unicodedata
from typing import List


def _is_lower(ch: str) -> bool:
    """True for a letter that is not upper case (lower case or caseless, such as CJK)."""
    return ch.isalpha() and not ch.isupper()


def _is_mark(ch: str) -> bool:
    """True for a combining mark (Unicode category M*), as in ADR 0001's "mark" class."""
    return unicodedata.category(ch).startswith("M")


def _next_base(name: str, start: int) -> str:
    """The first character of ``name`` at or after ``start`` that is not a mark, or ``""``.

    The case rules compare letters, not marks: in decomposed (NFD) text the accent of
    ``"É"`` sits between the ``"E"`` and the next letter, and must not hide it.
    """
    for ch in name[start:]:
        if not _is_mark(ch):
            return ch
    return ""


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase, kebab-case or snake_case name to snake_case.

    The name is split into words and the words are lower-cased and joined with ``_``.
    A new word starts:

    - after any run of characters that are neither letters nor digits (``-``, ``_``,
      spaces, dots, ...); those characters are dropped, so separators never repeat and
      never appear at either end (``"user--id"`` -> ``"user_id"``,
      ``"_private"`` -> ``"private"``);
    - at an upper-case letter that follows a lower-case letter or a digit
      (``"parseUrl"`` -> ``"parse_url"``, ``"utf8Decode"`` -> ``"utf8_decode"``);
    - at the last capital of a run of capitals that is followed by a lower-case letter,
      so acronyms stay whole (``"HTTPServer"`` -> ``"http_server"``).

    Digits never start a word on their own: they stay with the word they follow
    (``"parseURL2"`` -> ``"parse_url2"``, ``"HTTP2Server"`` -> ``"http2_server"``). Text
    with no case changes is never split, so snake_case input comes back unchanged
    (``"user_id"`` -> ``"user_id"``).

    Combining marks (Unicode category ``M*``) continue the word they follow, as in ADR
    0001, and are skipped when the case rules look at the letters around a capital; a mark
    with no word to attach to (at the start, or right after a separator) is dropped. So a
    name gives the same words whether it is composed (NFC) or decomposed (NFD). The text
    is not normalised: the result keeps the input's form. See ADR 0002 for the reasoning
    and more examples.

    Args:
        name: The identifier to convert. Any string is accepted; an empty string, or one
            with no letters or digits, gives ``""``.

    Returns:
        The snake_case form of ``name``: lower-case words joined by single underscores.

    Raises:
        TypeError: If ``name`` is not a ``str`` (checked up front, because iterating a
            list or bytes would otherwise give a confusing result or error).
    """
    if not isinstance(name, str):
        raise TypeError(f"to_snake_case() expects a str, got {type(name).__name__}")

    words: List[str] = []
    current: List[str] = []

    def flush() -> None:
        if current:
            words.append("".join(current))
            current.clear()

    for i, ch in enumerate(name):
        if _is_mark(ch):
            # A mark continues the word it follows (ADR 0001) and never starts one; with
            # no word open it has no base letter and is dropped.
            if current:
                current.append(ch)
            continue
        if not ch.isalnum():
            flush()
            continue
        if current and ch.isupper():
            # Compare base letters, skipping marks (NFD "É" is "E" + U+0301).
            # ``current`` always starts with a letter or digit, so this finds one.
            prev = next(c for c in reversed(current) if not _is_mark(c))
            nxt = _next_base(name, i + 1)
            if not prev.isupper():
                # lower/digit -> upper: "parseUrl", "utf8Decode".
                flush()
            elif _is_lower(nxt):
                # Inside a run of capitals, the last one belongs to the next word:
                # "HTTPServer" -> "HTTP" + "Server".
                flush()
        current.append(ch)
    flush()

    return "_".join(word.lower() for word in words)
