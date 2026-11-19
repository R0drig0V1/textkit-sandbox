"""String helpers. Every public function is listed in the README's function table."""

import re

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
