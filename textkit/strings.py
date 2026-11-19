"""String helpers. Every public function is listed in the README's function table."""

import re

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
