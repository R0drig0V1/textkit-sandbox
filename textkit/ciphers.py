"""Simple letter-substitution ciphers. Every public function is listed in the README's function
table."""

import string

# Built once at import: str.translate with a table is a single C-level pass over the text.
# Only the 52 ASCII letters are mapped, so every other character (digits, punctuation,
# non-ASCII letters such as "é") is left unchanged by translate.
_ROT13_TABLE = str.maketrans(
    string.ascii_lowercase + string.ascii_uppercase,
    string.ascii_lowercase[13:]
    + string.ascii_lowercase[:13]
    + string.ascii_uppercase[13:]
    + string.ascii_uppercase[:13],
)


def rot13(text: str) -> str:
    """Return ``text`` with every ASCII letter rotated by 13 places in the alphabet.

    Case is kept (``"a"`` -> ``"n"``, ``"N"`` -> ``"A"``). Every other character, non-ASCII
    letters included (``"é"``), is returned unchanged. Because the alphabet has 26 letters,
    the rotation is its own inverse: ``rot13(rot13(s)) == s`` for every string ``s``.

    Examples: ``rot13("Hello, World!") == "Uryyb, Jbeyq!"``, ``rot13("") == ""``.

    Raises:
        TypeError: ``text`` is not a ``str``.
    """
    # Checked explicitly so every non-str fails the same documented way; without it most
    # would raise AttributeError (no .translate) instead.
    if not isinstance(text, str):
        raise TypeError(f"rot13 expects a str, got {type(text).__name__}")
    return text.translate(_ROT13_TABLE)
