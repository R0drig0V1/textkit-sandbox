"""Byte sizes. Every public function is listed in the README's function table."""

# Binary (IEC) units, index k meaning 1024**k bytes. TiB is the largest: anything bigger is
# still shown in TiB (1024**5 is "1024.0 TiB"), so the table never needs to grow.
_UNITS = ("B", "KiB", "MiB", "GiB", "TiB")


def human_bytes(n: int) -> str:
    """Return the byte count ``n`` as a short human-readable string in binary units.

    The unit is the largest of B, KiB, MiB, GiB and TiB with ``n >= 1024**k``, chosen from
    ``n`` itself before any rounding, so ``1048575`` is ``"1024.0 KiB"``, not ``"1.0 MiB"``.
    Below 1024 the result is the exact count, ``f"{n} B"`` (``1023`` -> ``"1023 B"``); from
    KiB up it is ``n / 1024**k`` with one decimal (``1536`` -> ``"1.5 KiB"``, ``1024**4`` ->
    ``"1.0 TiB"``, ``1024**5`` -> ``"1024.0 TiB"``). The decimal uses Python's float
    formatting, which rounds half to even on the exact binary value (``1280`` ->
    ``"1.2 KiB"``).

    Raises ``ValueError`` if ``n`` is not an ``int`` (a ``bool`` included, a ``str`` or a
    ``float`` such as ``1.5`` too), if ``n`` is negative, or if ``n / 1024**k`` is too large
    for a float (``10**400``).
    """
    # bool is a subclass of int, so it is rejected explicitly; the type is checked before
    # the sign so that "a" gets ValueError, not a TypeError from the comparison.
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"human_bytes() needs an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"human_bytes() needs n >= 0, got {n}")
    # Pick the unit with integer comparisons, so the choice is exact for any size and does
    # not depend on how the quotient later rounds.
    k = 0
    while k + 1 < len(_UNITS) and n >= 1024 ** (k + 1):
        k += 1
    if k == 0:
        return f"{n} B"
    try:
        value = n / 1024**k
    except OverflowError:
        # int / int true division raises OverflowError when the quotient does not fit a
        # float; turn it into ValueError, the one error type callers (and the CLI) expect.
        raise ValueError(f"human_bytes() cannot represent {n} bytes as a float") from None
    return f"{value:.1f} {_UNITS[k]}"
