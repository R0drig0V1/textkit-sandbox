"""String helpers. Every public function is listed in the README's function table.

A rejected argument value raises ``textkit.errors.InvalidValueError`` (ADR 0006).
"""

import re
import unicodedata

from textkit.errors import InvalidValueError

# Compiled once: any run of characters outside lower-case ASCII letters and digits.
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


def squeeze(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip both ends."""
    return " ".join(text.split())


def slugify(text: str) -> str:
    """Turn ``text`` into a lower-case ASCII slug: ``"Hello, World!"`` -> ``"hello-world"``.

    Steps, in order:

    1. Every non-ASCII character is removed, with no separator left in its place
       (``"naïve"`` -> ``"nave"``). No Unicode normalization is applied, so the result
       depends on the input form: NFC ``"Ñandú"`` gives ``"and"`` while NFD ``"Ñandú"``
       (base letters plus combining marks) gives ``"nandu"``.
    2. The text is lower-cased.
    3. Every run of characters outside ``[a-z0-9]`` (``_`` included) becomes one ``-``.
    4. Leading and trailing ``-`` are stripped.

    Never raises for a ``str`` argument; ``""`` and punctuation-only input give ``""``.
    """
    # Filter by code point rather than str.isalnum, which accepts non-ASCII letters.
    ascii_only = "".join(ch for ch in text if ord(ch) < 128)
    return _NON_SLUG_RUN.sub("-", ascii_only.lower()).strip("-")


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` code points, marking the cut with ``suffix``.

    If ``len(text) <= width`` the text fits and is returned unchanged. Otherwise the start of
    ``text`` is kept and ``suffix`` appended so that the result, suffix included, is exactly
    ``width`` long.

    Raises:
        InvalidValueError: if ``width < len(suffix)``. This is checked first, so it is
            raised even when ``text`` would fit: an invalid width is a caller bug regardless
            of input.
    """
    if width < len(suffix):
        raise InvalidValueError(
            f"width ({width}) must be at least the suffix length ({len(suffix)})"
        )
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix


def strip_accents(text: str) -> str:
    """Remove combining marks (accents, diacritics) from ``text``.

    The text is decomposed to NFD so that precomposed letters such as ``"ñ"`` split into a
    base letter plus combining marks; every character whose
    ``unicodedata.combining`` class is non-zero is dropped, and the rest is recomposed to
    NFC (``"Ñandú"`` -> ``"Nandu"``). Recomposing keeps characters that NFD splits without
    any mark, such as Hangul syllables, in their usual composed form.

    Letters with no canonical decomposition keep their shape (``"ø"``, ``"ł"`` and ``"ß"``
    are returned unchanged): only marks are removed, nothing is transliterated. Never
    raises for a ``str`` argument; ``""`` gives ``""``.
    """
    decomposed = unicodedata.normalize("NFD", text)
    # combining() is non-zero exactly for the combining marks we want to drop; base
    # characters (class 0) are kept.
    base = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", base)


def wrap(text: str, width: int) -> list[str]:
    """Split ``text`` into lines of at most ``width`` characters, breaking at spaces.

    Words are filled greedily: each line takes as many words as fit, joined by one space.
    Runs of spaces between words collapse to one, leading and trailing spaces are dropped
    and no returned line starts or ends with the separating space. A word longer than
    ``width`` is never split: it gets a line of its own, longer than ``width``. Widths are
    counted in code points (``len``).

    Existing newlines (and every other character for which ``str.isspace()`` is true, such
    as tabs) are separators just like spaces, so the text is reflowed and no returned line
    contains a line break; see ADR 0003 (``docs/decisions/0003-wrap-existing-newlines.md``).

    ``wrap("", width)`` and whitespace-only input give ``[]``.

    Raises:
        InvalidValueError: if ``width < 1``, whatever ``text`` is.
    """
    if width < 1:
        raise InvalidValueError(f"width must be at least 1, got {width}")
    lines: list[str] = []
    current = ""
    # str.split() with no argument splits on any whitespace run and drops empty strings,
    # which gives the collapsing, stripping and newline rules in one step (ADR 0003).
    for word in text.split():
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
    """Slug of ``text`` at most ``max_len`` characters long that never ends in ``-``.

    Exactly ``truncate(slugify(text), max_len, suffix="")`` with trailing ``-`` stripped: a
    character cut, not a word cut (``("Hello, World!", 8)`` -> ``"hello-wo"``), so a cut
    that lands right after a separator drops it (``("Hello, World!", 6)`` -> ``"hello"``).
    The result may be ``""`` (``max_len == 0`` or a punctuation-only ``text``).

    Raises:
        InvalidValueError: if ``max_len < 0``.
    """
    # truncate would raise for a negative width too; checking here names our parameter.
    if max_len < 0:
        raise InvalidValueError(f"max_len ({max_len}) must not be negative")
    return truncate(slugify(text), max_len, suffix="").rstrip("-")


def is_palindrome(text: str) -> bool:
    """Return whether ``text`` reads the same backwards, ignoring case, accents and symbols.

    Steps, in order:

    1. Accents are removed with :func:`strip_accents` (``"Dábale"`` -> ``"Dabale"``).
    2. The text is case-folded with ``str.casefold`` (stronger than ``lower``: ``"ß"``
       becomes ``"ss"``).
    3. Only characters for which ``str.isalnum()`` is true are kept, so spaces,
       punctuation and ``_`` are ignored while digits and non-ASCII letters count.

    The remaining sequence is compared with its reverse. ``""`` and text with no
    alphanumeric characters give ``True`` (the empty sequence is its own reverse). Never
    raises for a ``str`` argument.
    """
    # strip_accents before casefold: casefold can expand characters (e.g. "İ" -> "i" plus a
    # combining dot), and stripping first keeps such marks out of the comparison.
    kept = [ch for ch in strip_accents(text).casefold() if ch.isalnum()]
    return kept == kept[::-1]


def dedent(text: str) -> str:
    """Remove the prefix of spaces and tabs common to every non-blank line of ``text``.

    Lines are split with ``str.splitlines(keepends=True)`` and each line ending is kept
    exactly as it was. That method ends a line at every character it treats as a line
    boundary, not only ``"\\n"``: ``"\\r\\n"``, ``"\\r"``, ``"\\x0b"``, ``"\\x0c"`` (form
    feed), ``"\\x1c"``-``"\\x1e"``, ``"\\x85"``, ``"\\u2028"`` and ``"\\u2029"`` end a line too
    (unlike the ``"\\n"``-only rule of other textkit helpers), so
    ``dedent("  a\\x0c  b")`` gives ``"a\\x0cb"``.

    A line made only of spaces and tabs (or empty) is blank: it does not count when the
    common prefix is computed, and it becomes empty, its line ending kept. The prefix is
    compared character by character, so a tab and a space are different: lines indented
    with ``"\\t"`` and with ``"    "`` share no prefix and are returned unchanged. A text
    with no final line ending keeps none. ``""`` gives ``""``; blank-only text gives just
    its line endings.

    Unlike ``textwrap.dedent``, nothing else is normalized (no tab expansion, no
    ``"\\r\\n"`` translation).

    Raises:
        TypeError: if ``text`` is not a ``str`` (``bytes`` included). No other input is
            rejected.
    """
    if not isinstance(text, str):
        raise TypeError(f"dedent() expects str, got {type(text).__name__}")
    # Each item is (content, ending): splitlines() on one line gives its content without
    # the ending, whatever boundary character ended it ([""] for a line that is only an
    # ending, never [] since the line is not empty).
    lines = []
    for line in text.splitlines(keepends=True):
        content = line.splitlines()[0]
        lines.append((content, line[len(content):]))
    prefix = None
    for content, _ in lines:
        if not content.strip(" \t"):
            continue  # blank lines do not constrain the prefix
        indent = content[: len(content) - len(content.lstrip(" \t"))]
        if prefix is None:
            prefix = indent
        else:
            # Shorten the prefix to the part both share, character by character.
            common = 0
            for a, b in zip(prefix, indent):
                if a != b:
                    break
                common += 1
            prefix = prefix[:common]
    cut = len(prefix) if prefix else 0
    parts = []
    for content, ending in lines:
        if not content.strip(" \t"):
            parts.append(ending)
        else:
            parts.append(content[cut:] + ending)
    return "".join(parts)


def center(text: str, width: int, fill: str = " ") -> str:
    """Pad ``text`` on both sides with ``fill`` so that it is ``width`` code points long.

    The padding ``width - len(text)`` is split in two halves; when it is odd, the extra
    ``fill`` goes on the right: ``center("ab", 5)`` gives ``" ab  "``. This differs from
    ``str.center``, which puts the extra character on the left in some cases
    (``"ab".center(5)`` is ``"  ab "``). A ``text`` of ``width`` code points or more is
    returned unchanged (never cut). Lengths are counted in code points (``len``).

    Raises:
        InvalidValueError: if ``len(fill) != 1`` or ``width < 0``. Both are checked
            first, so they are raised even when ``text`` is already ``width`` long or
            longer: a bad argument is a caller bug regardless of the input.
    """
    if len(fill) != 1:
        raise InvalidValueError(f"fill must be exactly one character, got {fill!r}")
    if width < 0:
        raise InvalidValueError(f"width ({width}) must not be negative")
    padding = width - len(text)
    if padding <= 0:
        return text
    # Floor division gives the left side the smaller half, so an odd extra goes right.
    left = padding // 2
    return fill * left + text + fill * (padding - left)


def levenshtein(a: str, b: str) -> int:
    """Return the edit distance between ``a`` and ``b``, counted over code points.

    The distance is the smallest number of single-code-point insertions, deletions and
    substitutions, each of cost 1, that turn ``a`` into ``b``:
    ``levenshtein("kitten", "sitting") == 3``. It is symmetric, ``levenshtein("", s)`` is
    ``len(s)``, and equal strings give 0. Code points are compared as they are: no Unicode
    normalization and no case folding, so NFC ``"é"`` and NFD ``"e\\u0301"`` are at
    distance 2.

    Time is ``O(len(a) * len(b))``; memory is two rows of ``min(len(a), len(b)) + 1``
    integers, never the full matrix.

    Raises:
        TypeError: if ``a`` or ``b`` is not a ``str`` (``bytes`` included). No other input
            is rejected.
    """
    for name, value in (("a", a), ("b", b)):
        if not isinstance(value, str):
            raise TypeError(f"levenshtein() expects str for {name}, got {type(value).__name__}")
    # The rows run over the shorter string, so memory follows the smaller length.
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # delete char_a
                    current[j - 1] + 1,  # insert char_b
                    previous[j - 1] + (char_a != char_b),  # substitute (free if equal)
                )
            )
        previous = current
    return previous[-1]
