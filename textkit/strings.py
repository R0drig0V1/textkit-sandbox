"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

# Runs of anything that is not a lower-case ASCII letter or digit become one "-" in a slug.
# An explicit ASCII class, not str.isalnum, which also accepts non-ASCII letters and digits.
_SLUG_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")

# Break points for wrap (ADR 0003): ASCII whitespace only, the same set textwrap uses, so a
# no-break space (U+00A0) keeps its meaning and stays inside its word.
_WRAP_SEPARATOR_RUN = re.compile(r"[ \t\n\r\v\f]+")


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


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` characters, ending in ``suffix`` when cut.

    Lengths are counted in code points (``len``). If ``len(text) <= width`` the text fits
    and is returned unchanged. Otherwise the start of ``text`` is kept and ``suffix`` is
    appended so that the result, suffix included, is exactly ``width`` long:
    ``truncate("Hello, World!", 8)`` -> ``"Hello..."``.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked first, even when ``text``
            would fit, so an invalid ``width``/``suffix`` pair fails on every input rather
            than only on the long ones. A negative ``width`` always raises.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the length of suffix ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at spaces.

    Words are filled greedily: each line takes as many words as fit, joined by one space.
    The rules, pinned by ADR 0003 (docs/decisions/0003-wrap-newlines.md):

    - Every ASCII whitespace character (space, tab, ``\\n``, ``\\r``, ``\\v``, ``\\f``)
      is a break point, and a run of them counts as one. Existing newlines are *not* kept:
      the text is reflowed as a single paragraph, as ``textwrap.wrap`` does. Non-ASCII
      whitespace such as the no-break space (U+00A0) is part of the word it sits in.
    - Leading and trailing whitespace is dropped; no line starts or ends with a space, and
      the space that separated two lines is in neither of them.
    - A word longer than ``width`` is never cut: it gets a line of its own, which is then
      longer than ``width``.
    - Width is counted in code points (``len``), so a combining mark counts as one.
    - Text with no words (``""``, spaces or newlines only) gives ``[]``.

    Raises:
        TypeError: if ``text`` is not a ``str`` or ``width`` is not an ``int``.
        ValueError: if ``width < 1``, whatever ``text`` is (``""`` included).
    """
    if not isinstance(text, str):
        raise TypeError(f"wrap() expects str text, got {type(text).__name__}")
    if not isinstance(width, int):
        raise TypeError(f"wrap() expects int width, got {type(width).__name__}")
    if width < 1:
        raise ValueError(f"wrap() width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    for word in _WRAP_SEPARATOR_RUN.split(text):
        if not word:  # empty pieces from leading or trailing whitespace
            continue
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
