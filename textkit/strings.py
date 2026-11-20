"""String helpers. Every public function is listed in the README's function table."""

import re


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, ending in ``suffix`` when cut.

    ``text`` is returned unchanged when it fits (``len(text) <= width``). Otherwise the
    result keeps the start of ``text`` followed by ``suffix`` and is exactly ``width``
    long. ``suffix=""`` gives a plain character cut.

    Raises:
        ValueError: if ``width < len(suffix)``, even when ``text`` already fits. The check
            comes first so that a bad ``width`` fails on every input, not only long ones.
    """
    if width < len(suffix):
        raise ValueError(f"width {width} is smaller than the suffix length {len(suffix)}")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug made of ``[a-z0-9]`` and ``-``.

    Characters outside ASCII are removed first, with no separator left in their place
    (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result depends
    on the input's form: NFC ``"Ñandú"`` gives ``"and"`` while NFD gives ``"nandu"``. The rest
    is lower-cased, every run of characters outside ``[a-z0-9]`` (``_`` included) becomes a
    single ``-``, and ``-`` is stripped from both ends (``"Hello, World!"`` ->
    ``"hello-world"``). Input with nothing left, such as ``""`` or ``"!!!"``, gives ``""``.
    Never raises for a ``str`` argument.
    """
    # An explicit ASCII class instead of str.isalnum, which also accepts non-ASCII letters.
    ascii_only = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
