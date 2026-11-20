"""String helpers. Every public function is listed in the README's function table."""

import re
import unicodedata
from typing import Optional

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

    ``"    a\\n      b\\n"`` -> ``"a\\n  b\\n"``. Lines are split with
    ``str.splitlines(keepends=True)`` and each line ending is kept exactly as it was. That
    split also ends a line at ``"\\r"``, ``"\\x0b"``, ``"\\x0c"``, ``"\\x1c"``-``"\\x1e"``,
    ``"\\x85"``, ``"\\u2028"`` and ``"\\u2029"``, not only at ``"\\n"`` and ``"\\r\\n"`` (the
    ``"\\n"``-only rule of the template and diff tools does not apply here).

    - A line made only of spaces and tabs (or empty) is *blank*: it does not count for the
      common prefix and becomes empty, its line ending kept.
    - The prefix is compared character by character, so a tab and a space are different
      characters: ``"\\ta\\n    b"`` has no common prefix and is returned unchanged.
    - Only spaces and tabs form the prefix; other whitespace (``"\\u3000"``, for example)
      ends it.

    ``""`` gives ``""``. Never raises for a ``str`` argument. Written without ``textwrap``,
    whose ``dedent`` splits lines at ``"\\n"`` only.
    """
    # Split each line into its body and the ending splitlines found, so endings such as
    # "\r\n" or "\x0c" are put back unchanged. A line from splitlines(keepends=True) is never
    # empty, so line.splitlines() always has one element (the body, possibly "").
    parts = []
    for line in text.splitlines(keepends=True):
        body = line.splitlines()[0]
        parts.append((body, line[len(body):]))

    prefix: Optional[str] = None
    for body, _ in parts:
        indent = body[: len(body) - len(body.lstrip(" \t"))]
        if indent == body:
            continue  # blank: spaces and tabs only, never part of the prefix
        if prefix is None:
            prefix = indent
        else:
            # Keep the longest common start of the two indents, character by character.
            common = 0
            while common < min(len(prefix), len(indent)) and prefix[common] == indent[common]:
                common += 1
            prefix = prefix[:common]

    cut = len(prefix) if prefix else 0
    out = []
    for body, ending in parts:
        if body.lstrip(" \t") == "":
            out.append(ending)
        else:
            out.append(body[cut:] + ending)
    return "".join(out)


def center(text: str, width: int, fill: str = " ") -> str:
    """Pad ``text`` on both sides with ``fill`` to ``width`` code points.

    The padding ``width - len(text)`` is split in two halves; when it is odd, the extra
    ``fill`` goes on the **right**: ``center("ab", 5) == " ab  "``. This is why it is not
    ``str.center``, which puts the extra character on the left for some lengths
    (``"ab".center(5) == "  ab "``). Widths are counted in code points (``len``).

    A ``text`` of ``width`` code points or more is returned unchanged, never cut.

    Raises:
        InvalidValueError: if ``len(fill) != 1`` or ``width < 0``. Both are checked first,
            so they are raised even when ``text`` is already ``width`` long or longer: a bad
            argument is a caller bug regardless of the text.
    """
    if len(fill) != 1:
        raise InvalidValueError(f"fill must be exactly one character, got {fill!r}")
    if width < 0:
        raise InvalidValueError(f"width must not be negative, got {width}")
    padding = width - len(text)
    if padding <= 0:
        return text
    # Floor division gives the smaller half to the left, so an odd extra goes right.
    left = padding // 2
    return fill * left + text + fill * (padding - left)


def levenshtein(a: str, b: str) -> int:
    """Return the edit distance between ``a`` and ``b``, counted over code points.

    The distance is the least number of single code point insertions, deletions and
    substitutions, each of cost 1, that turn ``a`` into ``b``
    (``levenshtein("kitten", "sitting") == 3``). It is symmetric
    (``levenshtein(a, b) == levenshtein(b, a)``), ``levenshtein("", s) == len(s)`` and it
    is 0 exactly when ``a == b``. No Unicode normalization is applied, so NFC ``"é"`` and
    its NFD form (``"e"`` plus a combining accent) are at distance 2.

    Time is ``O(len(a) * len(b))``; memory is two rows of ``min(len(a), len(b)) + 1``
    integers, not the full table. Never raises for ``str`` arguments.
    """
    # Keep the shorter text along the row: memory then grows with the shorter input only.
    if len(a) < len(b):
        a, b = b, a
    # previous[j] is the distance between the first i - 1 code points of a and the first
    # j of b; current is the row being filled for the first i code points of a.
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
