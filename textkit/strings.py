"""String helpers. Every public function is listed in the README's function table."""

import re

# Runs of anything outside the slug alphabet. An explicit ASCII class is used on purpose:
# str.isalnum and \w accept non-ASCII letters, which slugs must not contain.
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in order:

    1. Every non-ASCII character is removed, leaving no separator in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"``, while NFD ``"Ñandú"``
       (base letters plus combining marks) gives ``"nandu"``.
    2. The text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    ``"Hello, World!"`` gives ``"hello-world"``. Input with no ASCII letters or digits,
    such as ``""`` or ``"!!!"``, gives ``""``. Never raises for a ``str`` argument.
    """
    # Drop non-ASCII first so it never turns into a separator (step 1 above).
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    return _NON_SLUG_RUN.sub("-", ascii_text.lower()).strip("-")
