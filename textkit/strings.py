"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


# Explicit ASCII classes: str.isalnum and \w would also accept non-ASCII letters and digits.
_NON_ASCII = re.compile(r"[^\x00-\x7f]+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"``, while NFD input (base
       letters followed by combining marks) keeps the base letters and gives ``"nandu"``.
    2. The text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    Never raises for a ``str`` argument; ``""`` and punctuation-only input give ``""``.
    """
    # Remove non-ASCII before lower-casing: some non-ASCII characters lower-case to ASCII
    # (the Kelvin sign U+212A becomes "k"), and the spec drops them.
    ascii_text = _NON_ASCII.sub("", text).lower()
    return _NON_SLUG.sub("-", ascii_text).strip("-")


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, tildes, cedillas...) from ``text``.

    The text is decomposed with NFD, every character whose Unicode combining class is
    non-zero is dropped, and the rest is recomposed with NFC, so ``"Ñandú"`` gives
    ``"Nandu"`` whether the input is NFC or NFD. Characters with no canonical
    decomposition are kept as they are (``"ø"``, ``"ł"`` and ``"ß"`` are not letters plus
    a mark), and so are standalone spacing accents such as ``"´"``. Never raises for a
    ``str``; ``""`` gives ``""``.
    """
    # NFD splits precomposed letters into base + combining marks; NFC afterwards puts
    # back together anything else NFD split apart (Hangul syllables, for example).
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", kept)


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, ending with ``suffix`` when cut.

    ``text`` is returned unchanged when it fits (``len(text) <= width``). Otherwise the start
    of ``text`` is kept and ``suffix`` appended so that the result is exactly ``width`` long.
    Lengths are counted in code points (``len``), not grapheme clusters or display columns.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked before the fit test, so it
            raises even when ``text`` would fit: a width that cannot hold the suffix is a
            caller error regardless of the input (with ``suffix=""`` it means ``width < 0``).
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the length of suffix ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix
