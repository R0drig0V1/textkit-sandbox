"""String helpers. Every public function is listed in the README's function table."""

import re

# Compiled once: slugify runs these on every call. Character classes are spelled out in
# ASCII on purpose; `\w` and `str.isalnum` would accept non-ASCII letters and digits.
_NON_ASCII = re.compile(r"[^\x00-\x7f]")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"`` while NFD ``"Ñandú"``
       (base letters plus combining marks) gives ``"nandu"``.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    Never raises for a ``str`` argument; ``""`` and input with no ASCII letters or digits
    (``"!!!"``) give ``""``.
    """
    ascii_only = _NON_ASCII.sub("", text)
    return _NON_SLUG.sub("-", ascii_only.lower()).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result, suffix included, is exactly
    ``width`` code points long.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked before anything else, so it
            raises even when ``text`` would fit: the caller asked for a width the suffix can
            never fit in, which is a bug at the call site whatever the input.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) is smaller than the suffix length ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix
