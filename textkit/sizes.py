"""Size formatting helpers. Every public function is listed in the README's function table.

``human_bytes`` follows plan task T3.10 (docs/phases/phase-3-converters.md): binary units
(powers of 1024, IEC names), the unit chosen before rounding, one decimal from KiB up.
"""

# Index k is the unit for 1024**k bytes. TiB is the largest unit: bigger sizes stay in TiB
# (1024**5 -> "1024.0 TiB") instead of growing the table.
_UNITS = ("B", "KiB", "MiB", "GiB", "TiB")


def human_bytes(n: int) -> str:
    """Return the byte count ``n`` as a short human-readable size in binary units.

    The unit is the largest of B, KiB, MiB, GiB and TiB (powers of 1024) with
    ``n >= 1024**k``, chosen before rounding. Below 1024 the result is the exact count,
    ``f"{n} B"`` (``1023`` -> ``"1023 B"``); from KiB up it is ``n / 1024**k`` with one
    decimal, ``f"{value:.1f} <unit>"``. Because the unit is fixed first, a value just below
    the next unit can round up to 1024.0 in the current one (``1048575`` ->
    ``"1024.0 KiB"``), and sizes of 1024 TiB or more stay in TiB (``1024**5`` ->
    ``"1024.0 TiB"``). Rounding is Python's float formatting, so exact ties go to the even
    digit (``1280`` -> ``"1.2 KiB"``).

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included), if ``n`` is
    negative, or if ``n / 1024**k`` does not fit in a float (``10**400``).
    """
    # bool is a subclass of int, so it is rejected explicitly (phase-3 rule for int
    # parameters). ValueError, not TypeError, is what that rule asks for.
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"human_bytes() expects an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"human_bytes() expects n >= 0, got {n}")
    # Chosen on the exact integer, before any rounding, so 1048575 stays in KiB.
    k = 0
    while k + 1 < len(_UNITS) and n >= 1024 ** (k + 1):
        k += 1
    if k == 0:
        return f"{n} B"
    try:
        value = n / 1024**k
    except OverflowError as exc:
        # int / int raises OverflowError when the quotient is too large for a float; the
        # phase-3 contract allows only ValueError, KeyError or TypeError.
        raise ValueError(f"human_bytes() cannot format n={n}: too large") from exc
    return f"{value:.1f} {_UNITS[k]}"
