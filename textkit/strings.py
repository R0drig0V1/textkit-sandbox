"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

# Compiled once: any run of characters outside lower-case ASCII letters and digits.
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug: ``"Hello, World!"`` -> ``"hello-world"``.

    Steps, in order:

    1. Every non-ASCII character is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"`` while NFD ``"Ñandú"``
       (base letters plus combining marks) gives ``"nandu"``.
    2. The text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    Never raises for a ``str`` argument; ``""`` and punctuation-only input give ``""``.
    """
    # Filter by code point rather than str.isalnum, which accepts non-ASCII letters.
    ascii_only = "".join(ch for ch in text if ord(ch) < 128)
    return _NON_SLUG_RUN.sub("-", ascii_only.lower()).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text fits and is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result, suffix included, is exactly
    ``width`` long.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked first, so it is raised even
            when ``text`` would fit: an invalid width is a caller bug regardless of input.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the suffix length ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    The text is decomposed to NFD so that precomposed letters such as ``"ñ"`` split into a
    base letter plus combining marks; every character whose
    ``unicodedata.combining`` class is non-zero is dropped, and the rest is recomposed to
    NFC (``"Ñandú"`` -> ``"Nandu"``). Recomposing keeps characters that NFD splits without
    any mark, such as Hangul syllables, in their usual composed form.

    Letters with no canonical decomposition keep their shape (``"ø"``, ``"ł"`` and ``"ß"``
    are returned unchanged): only marks are removed, nothing is transliterated. Never
    raises for a ``str`` argument; ``""`` gives ``""``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    # combining() is non-zero exactly for the combining marks we want to drop; base
    # characters (class 0) are kept.
    base = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", base)


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at spaces.

    Words are filled greedily: each line takes as many words as fit, joined by one space.
    Runs of spaces between words collapse to one, leading and trailing spaces are dropped
    and no returned line starts or ends with the separating space. A word longer than
    ``width`` is never split: it gets a line of its own, longer than ``width``. Widths are
    counted in code points (``len``).

    Existing newlines (and every other character for which ``str.isspace()`` is true, such
    as tabs) are separators just like spaces, so the text is reflowed and no returned line
    contains a line break; see ADR 0003 (``docs/decisions/0003-wrap-existing-newlines.md``).

    ``wrap("", width)`` and whitespace-only input give ``[]``.

    Raises:
        ValueError: if ``width < 1``, whatever ``text`` is.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    # str.split() with no argument splits on any whitespace run and drops empty strings,
    # which gives the collapsing, stripping and newline rules in one step (ADR 0003).
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
