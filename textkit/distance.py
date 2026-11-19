"""String distance helpers. Every public function is listed in the README's function table."""


def levenshtein(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between ``a`` and ``b``.

    The distance is the smallest number of single-character insertions, deletions and
    substitutions, each of cost 1, that turn ``a`` into ``b``. Characters are compared as
    code points, with no case folding or Unicode normalization, so ``"A"`` and ``"a"`` differ
    and NFC and NFD forms of the same text may differ. The distance is symmetric,
    ``levenshtein("", "")`` is 0 and ``levenshtein("kitten", "sitting")`` is 3.

    Runs in O(len(a) * len(b)) time and O(min(len(a), len(b))) extra memory.

    Raises ``TypeError`` if ``a`` or ``b`` is not a ``str``.
    """
    # Check explicitly: other sequences (lists, bytes) would otherwise give a number too,
    # and the contract is text only.
    if not isinstance(a, str) or not isinstance(b, str):
        raise TypeError("levenshtein() arguments must be str")
    # The distance is symmetric, so keep the shorter string as the row to save memory.
    if len(a) < len(b):
        a, b = b, a
    # previous[j] is the distance between the prefix of a seen so far and b[:j].
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # delete ca
                    current[j - 1] + 1,  # insert cb
                    previous[j - 1] + (ca != cb),  # substitute, free when equal
                )
            )
        previous = current
    return previous[-1]
