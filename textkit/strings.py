"""String helpers. Every public function is listed in the README's function table."""

import re

# Runs of anything that is not an ASCII lower-case letter or digit; slugify applies it after
# dropping non-ASCII characters and lower-casing, so this is exactly "a separator run".
_SLUG_SEPARATORS = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a URL slug of ASCII lower-case letters, digits and ``-``.

    Steps, in this order:

    1. Every non-ASCII character is dropped. A dropped character does **not** separate
       words: ``"aéb"`` becomes ``"ab"`` and ``"café au lait"`` becomes ``"caf-au-lait"``.
       Remove the accents first (``unicodedata`` NFKD plus dropping combining marks) to
       keep the base letters (``"cafe-au-lait"``).
    2. The rest is lower-cased. Dropping comes first so that non-ASCII characters whose
       lower case is ASCII (the Kelvin sign ``"\\u212a"`` lower-cases to ``"k"``) are
       still dropped.
    3. Every run of characters other than ``a-z`` and ``0-9`` (spaces, punctuation,
       underscores, control characters) becomes one ``-``.
    4. ``-`` is stripped from both ends.

    Examples: ``"Hello, World!"`` -> ``"hello-world"``, ``"  --Top 10--  "`` ->
    ``"top-10"``.

    Failure modes: never raises for a ``str``. The result is the empty string when ``text``
    has no ASCII letter or digit (``""``, ``"!?"``, ``"日本"``), so callers that need a
    non-empty slug must check for it. A non-``str`` argument is not supported and raises
    ``AttributeError``.
    """
    ascii_only = text.encode("ascii", "ignore").decode("ascii")
    return _SLUG_SEPARATORS.sub("-", ascii_only.lower()).strip("-")
