"""Edit distances between strings (plan task T3.1, docs/phases/phase-3-converters.md).

``levenshtein`` is the classic Levenshtein distance: the fewest single-character insertions,
deletions and substitutions, each of cost 1, that turn one string into the other. Characters
are compared as Unicode code points with no normalization or case folding, so callers that
want ``"é"`` (NFC) to equal ``"é"`` (NFD) normalize first. Every public function is listed in
the README's function table.
"""


def levenshtein(a: str, b: str) -> int:
    """Return the Levenshtein distance between ``a`` and ``b``.

    The distance is the fewest single-character insertions, deletions and substitutions, each
    of cost 1, that turn ``a`` into ``b`` (``levenshtein("kitten", "sitting")`` is 3). It is
    symmetric, 0 exactly when ``a == b`` (``levenshtein("", "")`` is 0), and the length of the
    other string when one of them is empty. Transpositions are not a single edit
    (``levenshtein("ab", "ba")`` is 2).

    Characters are compared as code points: case matters and there is no Unicode
    normalization, so NFC ``"é"`` and NFD ``"é"`` (``e`` plus a combining accent) are at
    distance 2.

    Runs in ``O(len(a) * len(b))`` time and ``O(min(len(a), len(b)))`` extra memory.

    Raises ``TypeError`` if ``a`` or ``b`` is not a ``str``.
    """
    for name, value in (("a", a), ("b", b)):
        if not isinstance(value, str):
            raise TypeError(f"levenshtein() expects str for {name}, got {type(value).__name__}")
    # The distance is symmetric, so iterate over the longer string and keep one row of the
    # shorter one's length: the memory then follows the shorter string.
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)

    # previous[j] is the distance between the prefix of a processed so far and b[:j].
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # delete char_a
                    current[j - 1] + 1,  # insert char_b
                    previous[j - 1] + (char_a != char_b),  # substitute, free when equal
                )
            )
        previous = current
    return previous[-1]
