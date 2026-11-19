"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result, suffix included, is exactly
    ``width`` long (``truncate("Hello, World!", 8)`` -> ``"Hello..."``).

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked first, so it is raised even
            when ``text`` would fit: a width that cannot hold the suffix is a caller error
            regardless of the input.
    """
    if width < len(suffix):
        raise ValueError(f"width ({width}) is smaller than the suffix length ({len(suffix)})")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    The text is decomposed with Unicode canonical decomposition (NFD), every nonspacing
    combining mark (category ``Mn``) is dropped, and what remains is recomposed (NFC), so
    ``"Ñandú"`` gives ``"Nandu"`` whether the input is NFC or NFD.

    Only marks are removed: letters with no canonical decomposition stay as they are
    (``"ø"``, ``"ł"``, ``"ß"``, ``"æ"``), and the result is not ASCII-only. Nonspacing marks
    of every script are dropped, which also alters text in scripts that write vowels or
    other meaningful signs as marks (Devanagari, Hebrew points, Arabic harakat). Empty
    input gives ``""``. Never raises for a ``str``.
    """
    # NFD, not NFKD: compatibility characters (ligatures, superscripts, full-width forms)
    # are not accents and keep their identity. The final NFC re-joins what NFD split but
    # is not a mark, such as Hangul syllables decomposed into jamo.
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", kept)


# Compiled once: slugify runs these on every call. The second pattern works on the
# lower-cased, ASCII-only text, so `_` and every other punctuation mark count as separators.
_NON_ASCII = re.compile(r"[^\x00-\x7f]+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input's form: NFC ``"Ñandú"`` gives ``"and"``, while NFD ``"Ñandú"``
       (base letters plus combining marks) gives ``"nandu"``. Callers who want accents
       folded should pass the text through ``strip_accents`` first.
    2. The text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    ``str.isalnum`` is deliberately not used: it accepts non-ASCII letters and digits.

    Never raises for a ``str`` argument; ``""`` or text with no ASCII letters or digits
    (``"!!!"``) gives ``""``.
    """
    ascii_only = _NON_ASCII.sub("", text)
    return _NON_SLUG.sub("-", ascii_only.lower()).strip("-")


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at spaces.

    Words are greedily packed into lines joined by a single space; the separating space is
    never part of a line. Runs of spaces collapse to one and leading and trailing spaces are
    dropped, so ``wrap("", w)`` and ``wrap("   ", w)`` are ``[]``. A word longer than
    ``width`` is not split: it gets a line of its own, which is then longer than ``width``.

    Existing line breaks (``"\\n"``, ``"\\r"``, hence ``"\\r\\n"``) are treated as spaces and
    never appear in the result: the text is reflowed (ADR 0003). Other whitespace, such as
    tabs or non-breaking spaces, is not a break point and stays inside its word.

    Raises:
        ValueError: if ``width < 1``. Checked first, so it is raised even for empty text.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    # Line breaks become spaces before splitting (ADR 0003); filtering out the empty strings
    # that split(" ") yields for repeated, leading or trailing spaces collapses them.
    words = [w for w in text.replace("\r", " ").replace("\n", " ").split(" ") if w]
    lines: list[str] = []
    current = ""
    for word in words:
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


def slug_title(text: str, max_len: int) -> str:
    """Return ``slugify(text)`` cut to at most ``max_len`` characters, never ending in ``-``.

    Exactly ``truncate(slugify(text), max_len, suffix="")`` with trailing ``-`` stripped.
    The cut is by character, not by word: ``slug_title("Hello, World!", 8)`` gives
    ``"hello-wo"``, and ``slug_title("Hello, World!", 6)`` gives ``"hello"`` (the cut lands
    on the separator, which is then stripped). The result may be shorter than ``max_len``
    and may be ``""`` (``max_len == 0``, or text with no ASCII letters or digits).

    Raises:
        ValueError: if ``max_len < 0``.
    """
    # Checked here rather than left to truncate, whose message speaks of a suffix the
    # caller never passed.
    if max_len < 0:
        raise ValueError(f"max_len must be >= 0, got {max_len}")
    return truncate(slugify(text), max_len, suffix="").rstrip("-")


def is_palindrome(text: str) -> bool:
    """Return whether ``text`` reads the same forwards and backwards.

    Case, spaces, punctuation and accents are ignored: the text goes through
    ``strip_accents`` and then ``str.casefold()``, and only the characters for which
    ``str.isalnum()`` is true are kept and compared code point by code point. Digits count
    (``"12321"`` is a palindrome). ``""`` and text with no alphanumeric characters
    (``"!?"``) return ``True``: an empty sequence reads the same both ways. Never raises for
    a ``str``.
    """
    # strip_accents runs before casefold so that "Á" and "a" meet as "a". casefold may
    # still produce marks ("İ" -> "i" + U+0307); those are not alphanumeric and are dropped
    # by the filter, so the order of the steps is the one the plan pins.
    kept = [c for c in strip_accents(text).casefold() if c.isalnum()]
    return kept == kept[::-1]
