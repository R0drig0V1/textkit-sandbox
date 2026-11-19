"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


# Compiled once; ``re`` patterns are cheap to reuse and this keeps ``slugify`` readable.
_NON_ASCII = re.compile(r"[^\x00-\x7f]+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug such as ``"hello-world"``.

    Steps, in this order:

    1. Every character outside ASCII is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result depends
       on the input's form: NFC ``"Ñandú"`` gives ``"and"``, NFD ``"Ñandú"`` (base letter plus
       combining mark) gives ``"nandu"``. Normalize to NFD first to keep the base letters.
    2. The rest is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` and whitespace included) becomes
       one ``-``.
    4. ``-`` is stripped from both ends.

    Non-ASCII is removed *before* lower-casing so that characters such as the Kelvin sign
    (U+212A), which ``str.lower`` maps to ASCII ``"k"``, are dropped like any other non-ASCII
    character. ``str.isalnum`` is deliberately not used: it accepts non-ASCII letters and digits.

    Never raises for a ``str``; returns ``""`` when nothing alphanumeric is left (``""``,
    ``"!!!"``).
    """
    ascii_text = _NON_ASCII.sub("", text).lower()
    return _NON_SLUG.sub("-", ascii_text).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text fits and is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result is exactly ``width`` long; when
    ``width == len(suffix)`` the result is the suffix alone. Lengths count code points, so a
    combining sequence may be split.

    Raises:
        ValueError: if ``width < len(suffix)`` (with ``suffix=""`` that means a negative
            ``width``). This is checked before anything else, so it raises even when ``text``
            would fit: an invalid width is a caller bug whatever the input.
    """
    if width < len(suffix):
        raise ValueError(
            f"width ({width}) must be at least the length of suffix ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    ``"Ñandú"`` -> ``"Nandu"``, ``"Crème brûlée"`` -> ``"Creme brulee"``.

    The text is decomposed with canonical decomposition (NFD), every character whose
    ``unicodedata.combining`` class is non-zero is dropped, and the rest is recomposed
    with NFC. Consequences:

    - NFC and NFD input give the same result, and the result is always NFC.
    - Base letters with no canonical decomposition are left as they are: ``"ø"``,
      ``"ł"``, ``"đ"`` and ``"ß"`` are distinct letters, not accented ones, so
      ``"Søren Kierkegaard"`` stays ``"Søren Kierkegaard"`` and ``"straße"`` stays
      ``"straße"``. No transliteration is attempted.
    - Compatibility characters are not touched (NFD, not NFKD): ``"ﬁ"`` stays ``"ﬁ"``.
    - "Combining mark" means a non-zero canonical combining class, so the rule is about
      marks, not about accents: non-accent marks such as the Devanagari virama (U+094D) are
      removed too, while marks of class 0 such as spacing vowel signs (U+093F) and the
      combining enclosing circle (U+20DD) are kept.
    - Text without combining marks is returned unchanged apart from NFC normalization;
      Hangul syllables are decomposed and recomposed, so they come back intact.

    Never raises for a ``str`` argument; ``""`` gives ``""``.
    """
    # Decompose first so precomposed letters ("ñ" as U+00F1) expose their mark; recompose
    # at the end so that what is left (e.g. Hangul jamo) returns to its usual NFC form.
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", kept)


# Where ``wrap`` may break: any run of whitespace (``str.isspace``; ``re``'s ``\s`` matches
# the same set for ``str`` patterns), except the non-breaking spaces U+00A0, U+2007 and
# U+202F, which by definition forbid a break and so stay inside their word. See ADR 0003.
_BREAK = re.compile(r"[^\S\u00a0\u2007\u202f]+")


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking between words.

    Words are filled greedily: each line takes as many words as fit, joined by one space.
    Lengths are counted in code points (``len``).

    - Any run of whitespace separates words: spaces, tabs and newlines alike (ADR 0003).
      Existing newlines are therefore *not* kept; the text is reflowed as one paragraph. To
      keep paragraphs, split them first and wrap each one.
    - The non-breaking spaces U+00A0, U+2007 and U+202F are not separators; they count as
      ordinary characters of the word they are in.
    - Runs of separators collapse, separators at both ends are dropped, and no line starts
      or ends with whitespace that separated words.
    - A word longer than ``width`` is never split: it gets a line of its own, longer than
      ``width``.
    - Text with no words (``""``, ``"  \\n "``) gives ``[]``.

    Raises ``ValueError`` when ``width < 1``, even for empty ``text``.
    """
    if width < 1:
        raise ValueError(f"width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    for word in _BREAK.split(text):
        if not word:  # ``split`` yields "" when ``text`` starts or ends with a separator
            continue
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def slug_title(text: str, max_len: int) -> str:
    """Return a slug of ``text`` at most ``max_len`` characters long that never ends in ``-``.

    Exactly ``truncate(slugify(text), max_len, suffix="")`` with trailing ``-`` stripped: a
    character cut, not a word cut, so a word may be cut in the middle
    (``slug_title("Hello, World!", 8)`` -> ``"hello-wo"``). When the cut lands right after a
    separator the separator is dropped, so the result can be shorter than ``max_len``
    (``slug_title("Hello, World!", 6)`` -> ``"hello"``). ``slugify`` already strips ``-`` at
    the start and collapses runs of separators, so only one trailing ``-`` can be left by the
    cut.

    The result may be ``""``: when ``max_len`` is 0 or when ``text`` has nothing left after
    ``slugify``.

    Raises:
        ValueError: if ``max_len < 0``. Checked here, before ``truncate`` would raise the same
            exception type, so the message names ``max_len`` rather than ``suffix``.
    """
    if max_len < 0:
        raise ValueError(f"max_len ({max_len}) must not be negative")
    return truncate(slugify(text), max_len, suffix="").rstrip("-")


def is_palindrome(text: str) -> bool:
    """Return ``True`` if ``text`` reads the same backwards, ignoring everything but letters
    and digits.

    ``"A man, a plan, a canal: Panama!"`` and ``"Ánà"`` are palindromes; ``"hello"`` is not.

    ``text`` is normalized in this order, then compared with its reverse code point by code
    point:

    1. ``strip_accents`` removes combining marks, so ``"é"`` counts as ``"e"`` whether the
       input is NFC or NFD. Letters with no canonical decomposition stay distinct
       (``"ø"`` is not ``"o"``).
    2. ``str.casefold`` ignores case; it is stronger than ``lower`` (``"ß"`` becomes
       ``"ss"``, so ``"sß"`` is a palindrome).
    3. Only characters for which ``str.isalnum`` is true are kept: spaces, punctuation,
       ``_``, symbols and any marks left over are dropped. Digits count (``"12321"`` is a
       palindrome), and so do non-Latin letters and digits.

    Accents are stripped *before* casefolding because ``strip_accents`` is the documented
    accent rule of this package. A combining mark that casefolding could still introduce is
    not alphanumeric and is dropped in step 3, so no mark survives to the comparison.

    Never raises for a ``str`` argument. ``""`` and text with no alphanumeric characters
    (``"!!!"``, ``"   "``) return ``True``: an empty sequence equals its reverse.
    """
    kept = [c for c in strip_accents(text).casefold() if c.isalnum()]
    return kept == kept[::-1]
