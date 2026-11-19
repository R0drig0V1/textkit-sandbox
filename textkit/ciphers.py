"""Simple letter ciphers (plan task T3.2, docs/phases/phase-3-converters.md).

``rot13`` rotates the 26 ASCII letters by 13 places. Only ASCII letters move: accented and
other non-ASCII letters, digits, punctuation and whitespace pass through unchanged, so the
cipher is its own inverse on every string. Every public function is listed in the README's
function table.
"""

import string

# Built once at import: str.translate with a table is a single C-level pass over the text.
# The table maps only the 52 ASCII letters, so every other code point (``"é"``, ``"ß"``, the
# Kelvin sign U+212A) is left alone instead of being caught by str.isalpha or case mapping.
_ROT13 = str.maketrans(
    string.ascii_lowercase + string.ascii_uppercase,
    string.ascii_lowercase[13:]
    + string.ascii_lowercase[:13]
    + string.ascii_uppercase[13:]
    + string.ascii_uppercase[:13],
)


def rot13(text: str) -> str:
    """Return ``text`` with every ASCII letter rotated by 13 places, keeping its case.

    ``a``-``m`` become ``n``-``z`` and back (``"Hello, World!"`` -> ``"Uryyb, Jbeyq!"``);
    every other character, non-ASCII letters included, is unchanged. ``rot13(rot13(s)) == s``
    for every string ``s``, and ``rot13("") == ""``.

    Raises ``TypeError`` when ``text`` is not a ``str`` (``bytes`` included), instead of the
    ``AttributeError`` or silent byte handling that ``translate`` would give.
    """
    if not isinstance(text, str):
        raise TypeError(f"rot13() expects a str, not {type(text).__name__}")
    return text.translate(_ROT13)
