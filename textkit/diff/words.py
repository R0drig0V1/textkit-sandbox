"""``diff_words``: a word-by-word diff of two texts (plan task T3.6).

Words are those of ``textkit._tokens.words`` (the rule of ADR 0002), compared by their text
only (``token.text``, plan task T3.3), and matched by the same longest common subsequence
and tie rule as ``unified_diff`` (``lcs.py``; ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``).
"""

from typing import List, Tuple

from textkit._tokens import words
from textkit.diff.lcs import edit_script


def diff_words(a: str, b: str) -> List[Tuple[str, str]]:
    """Return the word-by-word diff that turns text ``a`` into text ``b``.

    The result is a list of ``(op, word)`` pairs in text order: ``("=", w)`` for a word
    kept from both texts, ``("-", w)`` for a word only in ``a`` and ``("+", w)`` for a word
    only in ``b``. Words are those of ADR 0002 (whitespace and punctuation between them are
    not compared and not returned); each is exactly as in its text, compared by its text
    only, so a change of case or accent is a change. The kept words are a longest common
    subsequence; in a run of changes, deletions come before insertions. ``("", "")`` gives
    ``[]``; equal texts give only ``"="`` pairs.

    The cost is that of ``unified_diff`` in words: ``O(n * m)`` time and memory in the
    numbers of words that differ.

    Raises:
        TypeError: if ``a`` or ``b`` is not a ``str``.
    """
    for name, value in (("a", a), ("b", b)):
        if not isinstance(value, str):
            raise TypeError(f"diff_words() expects str for {name}, got {type(value).__name__}")
    old = [token.text for token in words(a)]
    new = [token.text for token in words(b)]
    return [(op, new[j] if op == "+" else old[i]) for op, i, j in edit_script(old, new)]
