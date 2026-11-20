"""String helpers. Every public function is listed in the README's function table."""


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
