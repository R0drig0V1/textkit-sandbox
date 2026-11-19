"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata

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


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` characters, marking the cut with ``suffix``.

    If ``text`` fits (``len(text) <= width``, counted in code points) it is returned
    unchanged. Otherwise the start of ``text`` is kept and ``suffix`` appended so that the
    result, suffix included, is exactly ``width`` long: ``truncate("Hello, World!", 8)``
    gives ``"Hello..."``. Pass ``suffix=""`` for a plain cut.

    Raises:
        ValueError: if ``width < len(suffix)``. This is checked before the fit test, so it
            raises even when ``text`` would fit: a width that cannot hold the suffix is a
            caller error whatever the input (it also rejects any negative ``width``).
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the suffix length ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    The text is decomposed to NFD, every character with a non-zero canonical combining class
    (``unicodedata.combining``) is dropped, and the rest is recomposed to NFC, so
    ``"Ñandú"`` gives ``"Nandu"`` whether the input is NFC or NFD.

    Recomposing matters for scripts whose NFD form is not made of combining marks: Hangul
    syllables decompose into jamo, which are kept and must be joined back.

    Letters that are distinct characters rather than a base plus a mark (``"ø"``, ``"ł"``,
    ``"ß"``) have no decomposition and are returned unchanged; this is not a transliterator.
    Marks with combining class 0 (for example some Thai vowel signs) are kept too, since
    removing them would change the word rather than its accents. Never raises for a ``str``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", kept)


def is_palindrome(text: str) -> bool:
    """Tell whether ``text`` is a palindrome, ignoring case, accents and punctuation.

    ``text`` is normalized in this order, then compared with its reverse:

    1. :func:`strip_accents` removes combining marks (``"é"`` -> ``"e"``), so accented and
       unaccented spellings match.
    2. ``str.casefold()`` folds case more aggressively than ``lower()`` (``"ß"`` -> ``"ss"``).
    3. Only characters for which ``str.isalnum()`` is true are kept: spaces and punctuation
       are ignored, while digits and non-ASCII letters count.

    ``"A man, a plan, a canal: Panamá"`` and ``"12321"`` give ``True``. Text with nothing
    left after step 3, such as ``""`` or ``"!?"``, is a palindrome (the empty string equals
    its reverse). Never raises for a ``str`` argument.
    """
    # Accents go first so that casefold() sees base letters; the alphanumeric filter goes
    # last because casefold() can itself produce combining marks (e.g. "İ" -> "i̇").
    kept = [c for c in strip_accents(text).casefold() if c.isalnum()]
    return kept == kept[::-1]
