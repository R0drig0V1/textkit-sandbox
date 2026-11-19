"""String helpers. Every public function is listed in the README's function table."""

import re

# Runs of characters that cannot appear in a slug (used by slugify).
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"``, while NFD input (base
       letters followed by combining marks) keeps the base letters and gives ``"nandu"``.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. ``-`` is stripped from both ends.

    Never raises for a ``str`` argument; text with no ASCII letters or digits (``""``,
    ``"!!!"``) gives ``""``.
    """
    # Drop non-ASCII before lower-casing: some non-ASCII characters lower-case to ASCII
    # (for example the Kelvin sign U+212A becomes "k"), and the plan says they are removed.
    ascii_text = text.encode("ascii", "ignore").decode("ascii").lower()
    # A regex on an explicit ASCII class, not str.isalnum, which also accepts non-ASCII.
    return _NON_SLUG_RUN.sub("-", ascii_text).strip("-")
