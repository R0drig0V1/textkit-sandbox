"""Duration helpers. Every public function is listed in the README's function table.

``parse_duration`` is plan task T3.11 (docs/phases/phase-3-converters.md): compact durations
such as ``"1h30m"`` to whole seconds, with the grammar pinned by the phase-3 plan review
(docs/plan-reviews/2026-11-19-phase-3.md, finding F4).
"""

import re

# Hours, minutes and seconds, each optional, in that order. [0-9] and not \d: \d (like
# str.isdigit) also accepts non-ASCII digits such as "١". Units are lower case only.
_DURATION = re.compile(r"(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s)?")


def parse_duration(text: str) -> int:
    """Return the number of seconds in a compact duration such as ``"1h30m"``.

    ``text`` is made of an hours part ``<digits>h``, a minutes part ``<digits>m`` and a
    seconds part ``<digits>s``, in that order; each part is optional but at least one must
    be present (``"1h30m"`` -> 5400, ``"45s"`` -> 45, ``"2h5s"`` -> 7205). Digits are ASCII
    ``0-9`` only and units are lower case only. Values are not range-limited, and zeros and
    leading zeros are allowed (``"90m"`` -> 5400, ``"0s"`` -> 0, ``"01h"`` -> 3600). Nothing
    else is accepted: no whitespace (a trailing newline included), signs, decimals, bare
    numbers, repeated or reordered parts.

    Raises ``TypeError`` if ``text`` is not a ``str``, and ``ValueError`` if it is not a
    duration as described above (``""``, ``"1H"``, ``"1h 30m"``, ``"30m1h"``, ``"45"``...).
    """
    if not isinstance(text, str):
        raise TypeError(f"parse_duration() expects a str, got {type(text).__name__}")
    # fullmatch, not match with "$": "$" also matches before a trailing "\n".
    match = _DURATION.fullmatch(text)
    # The pattern matches "" with every group absent, so "at least one part" is checked here.
    if match is None or match.lastindex is None:
        raise ValueError(f"parse_duration() expects a duration such as '1h30m', got {text!r}")
    hours, minutes, seconds = (int(group or 0) for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds
