"""String helpers. Every public function is listed in the README's function table."""


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result, suffix included, is exactly
    ``width`` long (``truncate("Hello, World!", 8)`` -> ``"Hello..."``).

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked first, so it is raised even
            when ``text`` would fit: a width that cannot hold the suffix is a caller error
            regardless of the input.
    """
    if width < len(suffix):
        raise ValueError(f"width ({width}) is smaller than the suffix length ({len(suffix)})")
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix
