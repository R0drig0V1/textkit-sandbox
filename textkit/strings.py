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
