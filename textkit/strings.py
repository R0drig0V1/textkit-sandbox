"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

# Runs of anything that is not a lower-case ASCII letter or digit become one "-" in a slug.
# An explicit ASCII class, not str.isalnum, which also accepts non-ASCII letters and digits.
_SLUG_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every non-ASCII character is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input's form: NFC ``"Ñandú"`` gives ``"and"``, NFD gives ``"nandu"``
       (the combining marks are dropped, the base letters kept). Use ``strip_accents``
       first if accented letters should survive as their base letters.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` and whitespace included)
       becomes a single ``-``.
    4. ``-`` is stripped from both ends.

    Non-ASCII is removed before lower-casing so that characters such as the Kelvin sign
    (U+212A, which lower-cases to ASCII ``"k"``) do not leak into the slug.

    Never raises for a ``str``; the result may be ``""`` (``""`` or ``"!!!"``).
    """
    ascii_only = text.encode("ascii", "ignore").decode("ascii")
    return _SLUG_SEPARATOR_RUN.sub("-", ascii_only.lower()).strip("-")


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, tildes, diaereses...) from ``text``.

    The text is decomposed to NFD so that precomposed letters such as ``"ñ"`` split into a
    base letter and a combining mark, every character with a non-zero
    ``unicodedata.combining`` class is dropped, and the rest is recomposed to NFC.
    ``strip_accents("Ñandú") == "Nandu"``; NFC and NFD input give the same result.

    Letters whose accent-like look is not a combining mark (``"ø"``, ``"ł"``, ``"ß"``) are
    kept unchanged, as is text with no marks at all.

    Raises:
        TypeError: if ``text`` is not a ``str`` (raised by ``unicodedata.normalize``).
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    # Recompose so that characters NFD split without a mark (e.g. Hangul syllables into
    # jamo) come back in their usual composed form.
    return unicodedata.normalize("NFC", kept)
