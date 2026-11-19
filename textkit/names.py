"""Helpers for personal names. Every public function is listed in the README's function
table."""

import re

# Only spaces and hyphens separate the parts of a name; a run of them counts as one. Tabs
# and other whitespace are deliberately not separators, so the rule stays predictable.
_SEPARATORS = re.compile(r"[ -]+")


def initials(name: str) -> str:
    """Return the upper-cased initials of ``name``, with no separators.

    ``name`` is split on runs of spaces and hyphens (``re.split(r"[ -]+", name)``); empty
    parts are ignored. Each part contributes ``c.upper()`` for its first character ``c``
    with ``c.isalpha()``, which may be several characters (``"ß"`` gives ``"SS"``); a part
    with no letter contributes nothing. So ``"jean-luc picard"`` gives ``"JLP"``,
    ``"3d printer"`` gives ``"DP"`` and ``""`` gives ``""``.

    No Unicode normalization is applied: a decomposed (NFD) ``"é"`` is the letter ``"e"``
    followed by a combining mark, so it contributes ``"E"``, while the composed form
    contributes ``"É"``.

    Never raises for a ``str`` argument.
    """
    result = []
    for part in _SEPARATORS.split(name):
        for char in part:
            # The first letter of the part, skipping leading digits and punctuation.
            if char.isalpha():
                result.append(char.upper())
                break
    return "".join(result)
