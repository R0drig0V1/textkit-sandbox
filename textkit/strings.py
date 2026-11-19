"""String helpers. Every public function is listed in the README's function table."""

import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    ``text`` is returned unchanged when it fits (``len(text) <= width``). Otherwise the start
    of ``text`` is kept and ``suffix`` appended so that the result, suffix included, is
    exactly ``width`` long. Lengths are counted in code points, not grapheme clusters.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked before the fit test, so it
            raises even when ``text`` would fit: a width that cannot hold the suffix is a
            caller bug whatever the input happens to be.
    """
    if width < len(suffix):
        raise ValueError(f"width ({width}) is smaller than the suffix length ({len(suffix)})")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, tildes, diaeresis...) from ``text``.

    The text is decomposed to NFD, every combining character (``unicodedata.combining``
    non-zero) is dropped and the rest is recomposed to NFC, so ``"Ñandú"`` gives
    ``"Nandu"`` whether the input was typed in NFC or NFD. Characters without a
    decomposition are kept as they are (``"ß"``, ``"ø"`` and ``"æ"`` stay unchanged), and
    so is everything that is not a letter with a mark. Never raises for a ``str``.
    """
    # NFD splits precomposed letters ("ú" -> "u" + U+0301) so the marks can be dropped;
    # NFC afterwards recomposes whatever remains (e.g. Hangul) into its usual form.
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", kept)
