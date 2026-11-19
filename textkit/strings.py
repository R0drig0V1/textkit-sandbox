"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


# Compiled once; ``re`` patterns are cheap to reuse and this keeps ``slugify`` readable.
_NON_ASCII = re.compile(r"[^\x00-\x7f]+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in this order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result depends
       on the input's form: NFC ``"Ñandú"`` gives ``"and"``, NFD ``"Ñandú"`` (base letter plus
       combining mark) gives ``"nandu"``. Normalize to NFD first to keep the base letters.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` and whitespace included) becomes
       one ``-``.
    4. ``-`` is stripped from both ends.

    Non-ASCII is removed *before* lower-casing so that characters such as the Kelvin sign
    (U+212A), which ``str.lower`` maps to ASCII ``"k"``, are dropped like any other non-ASCII
    character. ``str.isalnum`` is deliberately not used: it accepts non-ASCII letters and digits.

    Never raises for a ``str``; returns ``""`` when nothing alphanumeric is left (``""``,
    ``"!!!"``).
    """
    ascii_text = _NON_ASCII.sub("", text).lower()
    return _NON_SLUG.sub("-", ascii_text).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text fits and is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result is exactly ``width`` long; when
    ``width == len(suffix)`` the result is the suffix alone. Lengths count code points, so a
    combining sequence may be split.

    Raises:
        ValueError: if ``width < len(suffix)`` (with ``suffix=""`` that means a negative
            ``width``). This is checked before anything else, so it raises even when ``text``
            would fit: an invalid width is a caller bug whatever the input.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the length of suffix ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    ``"Ñandú"`` -> ``"Nandu"``, ``"Crème brûlée"`` -> ``"Creme brulee"``.

    The text is decomposed with canonical decomposition (NFD), every character whose
    ``unicodedata.combining`` class is non-zero is dropped, and the rest is recomposed
    with NFC. Consequences:

    - NFC and NFD input give the same result, and the result is always NFC.
    - Base letters with no canonical decomposition are left as they are: ``"ø"``,
      ``"ł"``, ``"đ"`` and ``"ß"`` are distinct letters, not accented ones, so
      ``"Søren Kierkegaard"`` stays ``"Søren Kierkegaard"`` and ``"straße"`` stays
      ``"straße"``. No transliteration is attempted.
    - Compatibility characters are not touched (NFD, not NFKD): ``"ﬁ"`` stays ``"ﬁ"``.
    - "Combining mark" means a non-zero canonical combining class, so the rule is about
      marks, not about accents: non-accent marks such as the Devanagari virama (U+094D) are
      removed too, while marks of class 0 such as spacing vowel signs (U+093F) and the
      combining enclosing circle (U+20DD) are kept.
    - Text without combining marks is returned unchanged apart from NFC normalization;
      Hangul syllables are decomposed and recomposed, so they come back intact.

    Never raises for a ``str`` argument; ``""`` gives ``""``.
    """
    # Decompose first so precomposed letters ("ñ" as U+00F1) expose their mark; recompose
    # at the end so that what is left (e.g. Hangul jamo) returns to its usual NFC form.
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", kept)
