"""Helpers for personal names (plan task T3.8, docs/phases/phase-3-converters.md).

``initials`` turns a name into its upper-case initials (``"jean-luc picard"`` -> ``"JLP"``).
Only spaces and hyphens separate parts, so a hyphenated given name gives one initial per
half, as is usual in French and many other languages. There is no Unicode normalization:
the caller decides whether ``"é"`` arrives composed (NFC) or as ``"e"`` plus a combining
accent (NFD), and the result follows. Every public function is listed in the README's
function table.
"""

import re

# Spaces and hyphens only (not \s): a tab or a newline inside a name is not a separator, and
# a run of separators counts as one.
_SEPARATORS = re.compile(r"[ -]+")


def initials(name: str) -> str:
    """Return the upper-case initials of ``name``, with no separators.

    ``name`` is split on runs of spaces and hyphens (``"jean-luc picard"`` -> ``"JLP"``);
    empty parts, from leading, trailing or repeated separators, are ignored. Each part
    contributes ``c.upper()`` of its first character ``c`` for which ``c.isalpha()`` is true,
    so leading digits and punctuation are skipped (``"3d printer"`` -> ``"DP"``) and a part
    with no letter contributes nothing (``"- -"`` -> ``""``). ``c.upper()`` may be several
    characters (``"ßa"`` -> ``"SS"``). No Unicode normalization is applied: NFD ``"élodie"``
    starts with a bare ``e`` and gives ``"E"``, NFC ``"élodie"`` gives ``"É"``.

    ``""`` returns ``""``. Any ``str`` is accepted; a non-``str`` argument raises
    ``TypeError`` (from ``re.split``).
    """
    letters = []
    for part in _SEPARATORS.split(name):
        for char in part:
            if char.isalpha():
                letters.append(char.upper())
                break
    return "".join(letters)
