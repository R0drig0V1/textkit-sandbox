"""String helpers. Every public function is listed in the README's function table."""

import re

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
