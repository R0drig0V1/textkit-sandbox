"""Identifier case conversion helpers (snake_case, camelCase and friends).

The word-boundary rules used here are recorded in
docs/decisions/0002-snake-case-word-boundaries.md; every example in that ADR is tested in
tests/test_cases.py. ``to_camel_case`` and ``to_kebab_case`` split names with
``to_snake_case``, so they follow the same rules. Which characters are letters, digits or
combining marks comes from the shared tokenizer ``textkit._tokens.char_class`` (ADR 0001's
classes); the splitting itself is this module's own. Every public function is listed in the
README's function table.
"""

from typing import List

from textkit._tokens import DIGIT, LETTER, MARK, char_class


def _is_lower(ch: str) -> bool:
    """True for a letter that is not upper case (lower case or caseless, such as CJK)."""
    return ch.isalpha() and not ch.isupper()


def _is_mark(ch: str) -> bool:
    """True for a combining mark: ADR 0001's "mark" class, from the shared tokenizer."""
    return char_class(ch) == MARK


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
        cls = char_class(ch)
        if cls == MARK:
            # A mark continues the word it follows (ADR 0001) and never starts one; with
            # no word open it has no base letter and is dropped.
            if current:
                current.append(ch)
            continue
        if cls not in (LETTER, DIGIT):
            # Joiners and number separators separate here too: ADR 0002 shares ADR
            # 0001's classes but not its word regex ("kebab-case" is two words).
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


def to_camel_case(name: str) -> str:
    """Convert a snake_case, kebab-case, camelCase or PascalCase name to camelCase.

    The name is first split into words exactly as ``to_snake_case`` does (ADR 0002), then
    the first word is kept lower case and every later word gets its first character
    title-cased (``str.capitalize``); the words are joined with nothing in between
    (``"user_id"`` -> ``"userId"``, ``"kebab-case"`` -> ``"kebabCase"``). Splitting first,
    instead of only removing separators, means the ADR 0002 rules apply unchanged:

    - Leading, trailing and repeated separators are dropped (``"__user__id_"`` ->
      ``"userId"``, ``"-_- "`` -> ``""``).
    - Upper-case input is lower-cased word by word (``"USER_ID"`` -> ``"userId"``).
    - camelCase input comes back unchanged (``"userId"`` -> ``"userId"``); PascalCase
      input gets a lower-case first word (``"UserId"`` -> ``"userId"``). Acronyms are
      words too, so they are not kept in capitals: ``"HTTPServer"`` -> ``"httpServer"``,
      ``"parseURL"`` -> ``"parseUrl"`` (the round-trip cost noted in ADR 0002).
    - Digits stay with the word they follow; a word that is only digits joins the
      previous one, and a word that starts with a digit has nothing to capitalise
      (``"version_2_beta"`` -> ``"version2Beta"``, ``"utf8_decode"`` -> ``"utf8Decode"``,
      ``"user_2fa"`` -> ``"user2fa"``). So ``to_snake_case`` of the result can differ from
      the input (``"version2Beta"`` -> ``"version2_beta"``).
    - Combining marks stay with their base letter, and only the base letter is
      capitalised, so composed (NFC) and decomposed (NFD) input give the same result up
      to normalisation; the text is not normalised (``"naïve-über"`` -> ``"naïveÜber"``
      in either form). Caseless letters (CJK, ...) are left as they are.

    Args:
        name: The identifier to convert. Any string is accepted; an empty string, or one
            with no letters or digits, gives ``""``.

    Returns:
        The camelCase form of ``name``, with no separators.

    Raises:
        TypeError: If ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        # Checked here too so the message names this function, not to_snake_case.
        raise TypeError(f"to_camel_case() expects a str, got {type(name).__name__}")

    # to_snake_case drops every non-alphanumeric character, so "_" only ever joins words.
    words = to_snake_case(name).split("_")
    # The words are already lower case; capitalize() only title-cases the first
    # character, which in NFD text is the base letter, never a mark.
    return words[0] + "".join(word.capitalize() for word in words[1:])


def to_kebab_case(name: str) -> str:
    """Convert a camelCase, PascalCase, snake_case or kebab-case name to kebab-case.

    The name is split into words and lower-cased exactly as ``to_snake_case`` does (ADR
    0002), and the words are joined with ``-`` instead of ``_``. So every rule of ADR 0002
    applies unchanged:

    - Separators (any run of characters that are neither letters, digits nor combining
      marks) are dropped, so ``-`` never repeats and never appears at either end
      (``"user__id"`` -> ``"user-id"``, ``"_private"`` -> ``"private"``,
      ``"-_- "`` -> ``""``).
    - camelCase and PascalCase are split at case changes and acronyms stay whole
      (``"parseUrl"`` -> ``"parse-url"``, ``"HTTPServer"`` -> ``"http-server"``).
    - Digits stay with the word they follow (``"parseURL2"`` -> ``"parse-url2"``).
    - kebab-case input comes back unchanged (``"user-id"`` -> ``"user-id"``), and
      snake_case input only has its ``_`` replaced (``"user_id"`` -> ``"user-id"``).
    - Combining marks stay with their letter, so composed (NFC) and decomposed (NFD) input
      give the same words; the text is not normalised and keeps the input's form.

    Args:
        name: The identifier to convert. Any string is accepted; an empty string, or one
            with no letters or digits, gives ``""``.

    Returns:
        The kebab-case form of ``name``: lower-case words joined by single hyphens.

    Raises:
        TypeError: If ``name`` is not a ``str``.
    """
    if not isinstance(name, str):
        # Checked here too so the message names this function, not to_snake_case.
        raise TypeError(f"to_kebab_case() expects a str, got {type(name).__name__}")

    # Safe as a plain replace: to_snake_case drops every character that is not a letter,
    # digit or mark, "_" included, so in its output "_" only ever joins two words.
    return to_snake_case(name).replace("_", "-")
