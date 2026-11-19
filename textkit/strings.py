"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    ``text`` is returned unchanged when it fits (``len(text) <= width``). Otherwise the start
    of ``text`` is kept and ``suffix`` appended so that the result, suffix included, is
    exactly ``width`` long. Lengths are counted in code points, not grapheme clusters.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked before the fit test, so it
            raises even when ``text`` would fit: a width that cannot hold the suffix is a
            caller bug whatever the input happens to be.
    """
    if width < len(suffix):
        raise ValueError(f"width ({width}) is smaller than the suffix length ({len(suffix)})")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, tildes, diaeresis...) from ``text``.

    The text is decomposed to NFD, every combining character (``unicodedata.combining``
    non-zero) is dropped and the rest is recomposed to NFC, so ``"Ñandú"`` gives
    ``"Nandu"`` whether the input was typed in NFC or NFD. Characters without a
    decomposition are kept as they are (``"ß"``, ``"ø"`` and ``"æ"`` stay unchanged), and
    so is everything that is not a letter with a mark. Never raises for a ``str``.
    """
    # NFD splits precomposed letters ("ú" -> "u" + U+0301) so the marks can be dropped;
    # NFC afterwards recomposes whatever remains (e.g. Hangul) into its usual form.
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", kept)


# Anything that is not a lower-case ASCII letter or digit; `_` included on purpose.
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"``, NFD gives ``"nandu"``.
    2. The remaining text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. ``-`` is stripped from both ends.

    ``""`` and input with no ASCII letters or digits (``"!!!"``) give ``""``. Never raises
    for a ``str`` argument.
    """
    # Drop non-ASCII before lower-casing: some non-ASCII characters lower-case to ASCII
    # (KELVIN SIGN -> "k", "İ" -> "i" plus a combining dot), which would leak into the slug.
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    return _NON_SLUG_RUN.sub("-", ascii_text.lower()).strip("-")


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` code points, breaking at spaces.

    Words are separated by the space character ``" "`` and by line breaks. Existing line
    breaks (every boundary ``str.splitlines`` recognizes: ``\\n``, ``\\r\\n``, ``\\r`` and
    the rest) are not kept: they separate words exactly like a space, so the text is
    reflowed (ADR "`wrap` reflows text"). Runs of separators collapse to one, leading and
    trailing ones are dropped, and no returned line contains a separating space or a line
    break. Tabs, no-break spaces and other whitespace are not separators: they are part of
    a word.

    Lines are filled greedily: each word goes on the current line if it fits with one space
    before it, otherwise it starts a new line. A word longer than ``width`` gets a line of
    its own and is not split, so that line is longer than ``width``. Text with no words
    (``""``, only spaces or only line breaks) gives ``[]``.

    Raises:
        ValueError: if ``width < 1``. Checked first, so it raises even for ``""``.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    # splitlines() first so every kind of line break acts as a separator; split(" ") (not
    # split()) so that tabs and no-break spaces stay inside words, as the plan says "at spaces".
    words = [word for line in text.splitlines() for word in line.split(" ") if word]
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
