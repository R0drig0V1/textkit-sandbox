"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata
from typing import List

# Runs of anything that is not an ASCII lower-case letter or digit; slugify applies it after
# dropping non-ASCII characters and lower-casing, so this is exactly "a separator run".
_SLUG_SEPARATORS = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a URL slug of ASCII lower-case letters, digits and ``-``.

    Steps, in this order:

    1. Every non-ASCII character is dropped. A dropped character does **not** separate
       words: ``"aéb"`` becomes ``"ab"`` and ``"café au lait"`` becomes ``"caf-au-lait"``.
       Remove the accents first (``unicodedata`` NFKD plus dropping combining marks) to
       keep the base letters (``"cafe-au-lait"``).
    2. The rest is lower-cased. Dropping comes first so that non-ASCII characters whose
       lower case is ASCII (the Kelvin sign ``"\\u212a"`` lower-cases to ``"k"``) are
       still dropped.
    3. Every run of characters other than ``a-z`` and ``0-9`` (spaces, punctuation,
       underscores, control characters) becomes one ``-``.
    4. ``-`` is stripped from both ends.

    Examples: ``"Hello, World!"`` -> ``"hello-world"``, ``"  --Top 10--  "`` ->
    ``"top-10"``.

    Failure modes: never raises for a ``str``. The result is the empty string when ``text``
    has no ASCII letter or digit (``""``, ``"!?"``, ``"日本"``), so callers that need a
    non-empty slug must check for it. A non-``str`` argument is not supported and raises
    ``AttributeError``.
    """
    ascii_only = text.encode("ascii", "ignore").decode("ascii")
    return _SLUG_SEPARATORS.sub("-", ascii_only.lower()).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` characters, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text is returned unchanged. Otherwise the text is cut and
    ``suffix`` appended so that the result, suffix included, is exactly ``width`` characters
    long. An empty ``suffix`` gives a plain cut.

    Raises:
        ValueError: if ``width`` is smaller than ``len(suffix)`` (this includes any negative
            ``width``). The check runs before the length test, so it fails even when ``text``
            would fit: the contract depends only on ``width`` and ``suffix``, never on the
            input text.
    """
    if width < len(suffix):
        raise ValueError(
            f"width must be at least len(suffix) ({len(suffix)} for {suffix!r}), got {width}"
        )
    if len(text) <= width:
        return text
    # width - len(suffix) >= 0 here, so the slice never goes negative (which would count
    # from the end of the text instead of the start).
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks from ``text`` (``"Ñandú"`` -> ``"Nandu"``).

    The text is decomposed with Unicode NFD, every character of category ``Mn``
    (nonspacing combining mark) is dropped, and the rest is recomposed with NFC.

    Normalization form: NFD, not NFKD. NFKD also applies compatibility mappings
    (``"ﬁ"`` -> ``"fi"``, ``"²"`` -> ``"2"``, full-width letters -> ASCII), which
    change characters that carry no accent; this function only removes marks.
    The final NFC step matters for scripts that NFD splits without producing
    marks: Hangul syllables decompose into conjoining jamo (category ``Lo``), and
    without recomposition ``"한국"`` would come back as a different, longer string.

    Behaviour worth knowing:

    - Already-decomposed input (base letter + combining mark) gives the same
      result as precomposed input.
    - Text with no combining marks is returned unchanged (in NFC form).
    - Marks are removed in every script, not only Latin: Greek tonos
      (``"ά"`` -> ``"α"``), Cyrillic breve (``"й"`` -> ``"и"``) and Japanese
      dakuten (``"が"`` -> ``"か"``) are all ``Mn``. In those scripts this can
      change the letter, not just drop an accent.
    - Letters whose stroke or slash is part of the base character do not
      decompose and are kept: ``"ø"``, ``"ł"``, ``"đ"``, ``"ß"``.
    - Spacing combining marks (``Mc``, e.g. Devanagari vowel signs) and
      enclosing marks (``Me``) are kept, since removing them breaks the text.

    Never raises for a ``str`` argument; the empty string returns ``""``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", kept)


def wrap(text: str, width: int) -> List[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at whitespace.

    The rules are those of ADR 0003
    (``docs/decisions/0003-wrap-line-breaks-and-whitespace.md``):

    - **Existing line breaks are kept.** ``text`` is first cut at the line boundaries of
      ``str.splitlines`` (``"\\n"``, ``"\\r\\n"``, ``"\\r"`` and the other Unicode line
      separators); each source line is wrapped on its own and no output line spans two of
      them. A final line break does not add an empty line (``"a\\n"`` -> ``["a"]``).
    - **A source line with no words gives one empty string**, so blank lines survive:
      ``"a\\n\\nb"`` -> ``["a", "", "b"]``, and ``"\\n".join(result)`` keeps the
      paragraph layout.
    - **Inside a line, any run of whitespace** (spaces, tabs, other Unicode whitespace) is
      one word separator: runs collapse, leading and trailing whitespace is dropped, and
      words in an output line are joined by exactly one space. Tabs are not expanded.
    - **Greedy filling:** each output line takes as many words as fit in ``width``
      characters (code points).
    - **A word longer than ``width``** is not broken: it gets a line of its own, longer than
      ``width``.

    Examples: ``wrap("the quick brown fox", 10)`` -> ``["the quick", "brown fox"]``;
    ``wrap("", 10)`` -> ``[]``; ``wrap("   ", 10)`` -> ``[""]``.

    Failure modes: ``width <= 0`` raises ``ValueError`` (checked first, even for empty
    ``text``). The result is ``[]`` only for text with no lines at all (``""``). A
    non-``str`` ``text`` is not supported and raises ``AttributeError``.
    """
    if width <= 0:
        raise ValueError(f"width must be at least 1, got {width!r}")
    lines: List[str] = []
    for source_line in text.splitlines():
        current = ""
        for word in source_line.split():
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= width:
                current += " " + word
            else:
                lines.append(current)
                current = word
        # Appended even when empty: a blank source line stays a blank output line.
        lines.append(current)
    return lines
