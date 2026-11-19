"""String helpers. Every public function is listed in the README's function table."""


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())
