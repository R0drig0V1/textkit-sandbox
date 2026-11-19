"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

# Runs of anything outside lower-case ASCII letters and digits; used by slugify after the
# text has been reduced to ASCII and lower-cased, so `_` and punctuation count as separators.
_SLUG_SEPARATORS = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input's form: NFC ``"Ñandú"`` gives ``"and"``, while NFD input, whose
       accents are separate combining marks, gives ``"nandu"``.
    2. The remaining text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` and whitespace included) becomes
       a single ``-``.
    4. ``-`` is stripped from both ends.

    Never raises for a ``str``; ``""`` and punctuation-only input give ``""``.
    """
    # Filter by code point rather than with str.isalnum, which accepts non-ASCII letters
    # and digits; removing them first also keeps lower() from producing non-ASCII output.
    ascii_text = "".join(ch for ch in text if ord(ch) < 128)
    return _SLUG_SEPARATORS.sub("-", ascii_text.lower()).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, ending it with ``suffix`` if cut.

    ``text`` is returned unchanged when it fits (``len(text) <= width``). Otherwise the start
    of ``text`` is kept and ``suffix`` appended, so that the result, suffix included, is
    exactly ``width`` long. Lengths are counted in code points, as ``len`` does.

    Raises ``ValueError`` when ``width < len(suffix)``, even if ``text`` would fit: the check
    depends only on the arguments' shape, so a caller's bad ``width`` fails on every input
    instead of only on long ones. With ``suffix=""`` this means a negative ``width`` raises.
    """
    if width < len(suffix):
        raise ValueError(f"width {width} is smaller than the suffix length {len(suffix)}")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, tildes, umlauts...) from ``text``.

    The text is decomposed to NFD so that precomposed letters such as ``"ñ"`` split into a
    base letter plus a combining mark, then every combining character (non-zero
    ``unicodedata.combining`` class) is dropped: ``strip_accents("Ñandú") == "Nandu"``.

    The result is recomposed to NFC. Without that step, characters that decompose into
    parts that are not marks would come back split: Hangul syllables (``"한"``) would be
    returned as separate jamo. Letters that are not a base letter plus a mark (``"ø"``,
    ``"ß"``, ``"æ"``) are kept unchanged. Never raises for a ``str`` input; ``""`` gives
    ``""``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", stripped)


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at whitespace.

    Words are packed greedily: each line takes as many words as fit, joined by one space.
    A word longer than ``width`` is never cut; it gets a line of its own, which is then the
    only line longer than ``width``. Runs of whitespace collapse to one separator, leading
    and trailing whitespace is dropped, and no line contains the separating space.

    Existing newlines (and every other character for which ``str.isspace()`` is true, tabs
    and no-break spaces included) are word separators like a space, so the text is reflowed
    and no returned line contains a newline; see docs/decisions/0005-wrap-existing-newlines.md.

    ``wrap("", w)`` and whitespace-only input return ``[]``.

    Raises:
        ValueError: if ``width < 1``, whatever ``text`` is.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    # str.split() with no argument splits on runs of any whitespace and drops empty strings,
    # which gives the collapsing and the newline rule of
    # docs/decisions/0005-wrap-existing-newlines.md in one step.
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
