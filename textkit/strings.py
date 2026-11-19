"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

# Compiled once: slugify runs these on every call. Character classes are spelled out in
# ASCII on purpose; `\w` and `str.isalnum` would accept non-ASCII letters and digits.
_NON_ASCII = re.compile(r"[^\x00-\x7f]")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"`` while NFD ``"Ñandú"``
       (base letters plus combining marks) gives ``"nandu"``.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    Never raises for a ``str`` argument; ``""`` and input with no ASCII letters or digits
    (``"!!!"``) give ``""``.
    """
    ascii_only = _NON_ASCII.sub("", text)
    return _NON_SLUG.sub("-", ascii_only.lower()).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result, suffix included, is exactly
    ``width`` code points long.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked before anything else, so it
            raises even when ``text`` would fit: the caller asked for a width the suffix can
            never fit in, which is a bug at the call site whatever the input.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) is smaller than the suffix length ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    ``"Ñandú"`` -> ``"Nandu"``. The text is decomposed to NFD so that precomposed
    characters (``"ú"``, U+00FA) split into a base character plus combining marks, then
    every code point with a non-zero canonical combining class is dropped. Works the same
    for NFC and NFD input. Characters with no decomposition (``"ø"``, ``"ß"``, ``"ł"``)
    are kept as they are: they are distinct letters, not a base letter plus a mark.
    The result is recomposed to NFC, so text with nothing to strip (Hangul, CJK, ASCII)
    comes back in NFC form rather than split into decomposed pieces.
    Never raises for a ``str`` argument; ``""`` gives ``""``.
    """
    # NFD first: a precomposed letter carries its accent inside one code point, so
    # filtering combining marks without decomposing would miss it.
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    # NFC again: NFD also splits characters that carry no accent (a Hangul syllable
    # becomes its jamo), and callers expect those back untouched.
    return unicodedata.normalize("NFC", stripped)


def slug_title(text: str, max_len: int) -> str:
    """Build a slug of ``text`` at most ``max_len`` characters long that never ends in ``-``.

    Exactly ``truncate(slugify(text), max_len, suffix="")`` with trailing ``-`` stripped.
    The cut is by character, not by word, so a word can be split
    (``slug_title("Hello, World!", 8)`` -> ``"hello-wo"``); a cut that lands just after a
    separator drops it (``slug_title("Hello, World!", 6)`` -> ``"hello"``). The result can
    be ``""`` (``max_len == 0``, or input with no ASCII letters or digits).

    Raises:
        ValueError: if ``max_len < 0``.
    """
    # truncate would also raise here (width < len("")), but its message talks about a
    # suffix the caller never passed; name the argument the caller actually gave.
    if max_len < 0:
        raise ValueError(f"max_len ({max_len}) must not be negative")
    return truncate(slugify(text), max_len, suffix="").rstrip("-")


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at spaces.

    Words are packed greedily: each line takes as many words as fit, joined by one space;
    the separating space is never part of a line. Every whitespace character (as defined by
    ``str.isspace``) separates words, newlines included, so existing line breaks are
    reflowed, not kept (ADR 0003). Runs of whitespace collapse to one separator, and
    leading and trailing whitespace is dropped.

    A word longer than ``width`` is never split: it gets a line of its own, longer than
    ``width``. ``""`` and whitespace-only input give ``[]``.

    Raises ``ValueError`` when ``width < 1``, whatever ``text`` is.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    # str.split() with no argument does the collapsing and stripping (ADR 0003).
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
