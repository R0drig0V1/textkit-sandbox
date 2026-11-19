"""String helpers. Every public function is listed in the README's function table."""

import re


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
