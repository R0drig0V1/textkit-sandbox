"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, ending in ``suffix`` when cut.

    ``text`` is returned unchanged when it fits (``len(text) <= width``). Otherwise the
    result keeps the start of ``text`` followed by ``suffix`` and is exactly ``width``
    long. ``suffix=""`` gives a plain character cut.

    Raises:
        ValueError: if ``width < len(suffix)``, even when ``text`` already fits. The check
            comes first so that a bad ``width`` fails on every input, not only long ones.
    """
    if width < len(suffix):
        raise ValueError(f"width {width} is smaller than the suffix length {len(suffix)}")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug made of ``[a-z0-9]`` and ``-``.

    Characters outside ASCII are removed first, with no separator left in their place
    (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result depends
    on the input's form: NFC ``"Ñandú"`` gives ``"and"`` while NFD gives ``"nandu"``. The rest
    is lower-cased, every run of characters outside ``[a-z0-9]`` (``_`` included) becomes a
    single ``-``, and ``-`` is stripped from both ends (``"Hello, World!"`` ->
    ``"hello-world"``). Input with nothing left, such as ``""`` or ``"!!!"``, gives ``""``.
    Never raises for a ``str`` argument.
    """
    # An explicit ASCII class instead of str.isalnum, which also accepts non-ASCII letters.
    ascii_only = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")


def slug_title(text: str, max_len: int) -> str:
    """Make a slug of ``text`` at most ``max_len`` characters long that never ends in ``-``.

    Exactly ``truncate(slugify(text), max_len, suffix="")`` with trailing ``-`` stripped: a
    character cut, not a word cut, so a word may be split (``("Hello, World!", 8)`` ->
    ``"hello-wo"``), and a cut that lands right after a separator drops it
    (``("Hello, World!", 6)`` -> ``"hello"``). The result may be shorter than ``max_len`` and
    may be ``""`` (``max_len == 0``, or input that slugifies to nothing).

    Raises:
        ValueError: if ``max_len < 0``.
    """
    # Checked here so the error names this function's argument rather than truncate's.
    if max_len < 0:
        raise ValueError(f"max_len must be >= 0, got {max_len}")
    return truncate(slugify(text), max_len, suffix="").rstrip("-")


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    ``"Ñandú"`` becomes ``"Nandu"``. The text is decomposed to NFD, every character with a
    non-zero canonical combining class is dropped, and the rest is recomposed to NFC.
    Works the same for NFC and NFD input. Letters that are distinct base characters
    rather than a base plus a mark (``"ø"``, ``"ł"``, ``"ß"``) are kept unchanged. Never
    raises for a ``str``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Recompose so that characters NFD split without any mark to drop (Hangul syllables,
    # for example) come back in their usual composed form.
    return unicodedata.normalize("NFC", kept)


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` code points, breaking at whitespace.

    Words are filled greedily: each line takes as many words as fit, joined by one space.
    Runs of whitespace between words collapse to one separator and leading and trailing
    whitespace is dropped, so no line starts or ends with a space. Existing newlines (and
    any other ``str.isspace()`` character, such as tabs) are separators like a space, so
    the text is reflowed rather than kept in its original lines (ADR 0003). A word longer
    than ``width`` is never split: it gets a line of its own, longer than ``width``.
    ``wrap("", w)`` and whitespace-only input give ``[]``.

    Raises:
        ValueError: if ``width < 1``, checked first so that it fails on every input,
            including ``""``.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    # str.split() with no argument splits on every whitespace run and drops empty strings,
    # which gives the collapsing, the trimming and the newline rule of ADR 0003 at once.
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
