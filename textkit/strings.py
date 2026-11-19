"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

# Runs of characters that cannot appear in a slug (used by slugify).
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"``, while NFD input (base
       letters followed by combining marks) keeps the base letters and gives ``"nandu"``.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. ``-`` is stripped from both ends.

    Never raises for a ``str`` argument; text with no ASCII letters or digits (``""``,
    ``"!!!"``) gives ``""``.
    """
    # Drop non-ASCII before lower-casing: some non-ASCII characters lower-case to ASCII
    # (for example the Kelvin sign U+212A becomes "k"), and the plan says they are removed.
    ascii_text = text.encode("ascii", "ignore").decode("ascii").lower()
    # A regex on an explicit ASCII class, not str.isalnum, which also accepts non-ASCII.
    return _NON_SLUG_RUN.sub("-", ascii_text).strip("-")


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at spaces.

    Words are packed greedily: each line takes as many words as fit, joined by one space.
    Runs of spaces between words collapse to one, leading and trailing spaces are dropped,
    and no line contains the space that separated it from the next. A word longer than
    ``width`` is not split: it gets a line of its own, longer than ``width``.

    Existing line breaks (``"\\n"``, ``"\\r\\n"``, ``"\\r"``) are treated like spaces, so the
    text is reflowed and no returned line contains a newline (ADR 0001). Only spaces and
    line breaks separate words; tabs and other whitespace stay inside the word. Widths are
    counted in code points.

    ``wrap("", width)`` and text made only of spaces and line breaks give ``[]``.

    Raises:
        ValueError: if ``width < 1``.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    # Line breaks become spaces first (ADR 0001); "\r\n" before "\r" so it counts once.
    flat = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    # split(" ") rather than split(): only spaces separate words, not tabs or NBSP.
    words = [w for w in flat.split(" ") if w]
    lines: list[str] = []
    current = ""
    for word in words:
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


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, ending with ``suffix`` if cut.

    ``text`` is returned unchanged when it fits, that is when ``len(text) <= width``.
    Otherwise the start of ``text`` is kept and ``suffix`` appended so that the result is
    exactly ``width`` long.

    Raises:
        ValueError: if ``width < len(suffix)``, even when ``text`` would fit. The check comes
            first so that a bad ``width``/``suffix`` pair fails the same way for every input,
            instead of only when a long text happens to arrive.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the length of suffix ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks such as accents and diacritics from ``text``.

    The text is decomposed to NFD, every character with a non-zero canonical combining
    class (``unicodedata.combining``) is dropped, and the rest is recomposed to NFC:
    ``"Ñandú"`` -> ``"Nandu"``, whether the input is NFC or NFD. Recomposing keeps scripts
    whose NFD form is not marks (Hangul syllables, for example) as they were.

    Letters with no canonical decomposition are kept unchanged (``"ø"``, ``"ł"``, ``"ß"``),
    as are marks whose combining class is 0. Never raises for a ``str``; ``""`` gives ``""``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", kept)


def slug_title(text: str, max_len: int) -> str:
    """Make a slug of ``text`` at most ``max_len`` characters long that never ends in ``-``.

    Exactly ``truncate(slugify(text), max_len, suffix="")`` with trailing ``-`` stripped:
    the slug is cut at a character, not at a word boundary, so ``("Hello, World!", 8)``
    gives ``"hello-wo"``; when the cut lands just after a ``-``, it is dropped
    (``("Hello, World!", 6)`` gives ``"hello"``). The result may be ``""``, for example
    with ``max_len == 0`` or text with no ASCII letters or digits.

    Raises:
        ValueError: if ``max_len < 0``.
    """
    # truncate would also raise for a negative width (it is below len("")), but its message
    # talks about the suffix, which this function's callers never pass.
    if max_len < 0:
        raise ValueError(f"max_len must be at least 0, got {max_len}")
    return truncate(slugify(text), max_len, suffix="").rstrip("-")
