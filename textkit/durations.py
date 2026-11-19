"""Helpers for durations written as text. Every public function is listed in the README's
function table."""

import re

# ASCII digits are spelled out as [0-9]: \d and str.isdigit also accept non-ASCII digits
# such as "١" (ARABIC-INDIC DIGIT ONE). Units are lower case only and come in h, m, s order.
_DURATION = re.compile(r"(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s)?")


def parse_duration(text: str) -> int:
    """Return the number of seconds in a duration such as ``"1h30m"``.

    ``text`` is made of up to three parts, in this order: hours (``<digits>h``), minutes
    (``<digits>m``) and seconds (``<digits>s``). Each part is optional, but at least one
    must be present. Digits are ASCII only, units are lower case only, and nothing else is
    allowed: no spaces, signs, decimals or trailing newline. Values are not range-limited
    and zero and leading zeros are allowed, so ``"90m"`` gives ``5400``, ``"0s"`` gives
    ``0`` and ``"01h"`` gives ``3600``.

    Raises ``ValueError`` for any other text, for example ``""``, ``"45"``, ``"1H"``,
    ``"1h 30m"``, ``"30m1h"``, ``"1h1h"``, ``"1.5h"``, ``"-1h"`` or ``"45s\\n"``.
    """
    # fullmatch, not match with "$": "$" also matches before a trailing newline.
    match = _DURATION.fullmatch(text)
    if match is None or match.group(0) == "":
        raise ValueError(f"not a duration: {text!r}")
    hours, minutes, seconds = (int(group) if group else 0 for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds
