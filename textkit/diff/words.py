"""``diff_words``: the differences between two texts, word by word (plan task T3.6).

The words are those of ``textkit._tokens.words`` (the word rule of ADR 0002), compared by
their text only, and the edit script is the one ``lcs.edit_script`` gives for lines, with
the same tie rule (see the ADR ``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``).
"""

from typing import List, Tuple

from textkit import _tokens
from textkit.diff.lcs import edit_script


def diff_words(a: str, b: str) -> List[Tuple[str, str]]:
    """Return the word-level differences from ``a`` to ``b`` as ``(op, word)`` pairs.

    The words of each text are those of the word rule of ADR 0002 (what ``word_count``
    counts), each exactly as it appears in its text; whitespace and punctuation between
    words are not compared and not returned. The pairs are in order: ``("=", word)`` for a
    word kept from ``a`` to ``b``, ``("-", word)`` for a word of ``a`` that ``b`` drops and
    ``("+", word)`` for a word that ``b`` adds. The ``"="`` words are a longest common
    subsequence of the two word lists, compared exactly (case and accents count); in a run
    of changes the ``"-"`` words come first, and ties are broken as in ``unified_diff``.
    Reading the ``"="`` and ``"-"`` words gives the words of ``a``; the ``"="`` and ``"+"``
    words give those of ``b``. Two texts without words give ``[]``.

    Raises:
        TypeError: if ``a`` or ``b`` is not a ``str``.
    """
    for name, value in (("a", a), ("b", b)):
        if not isinstance(value, str):
            raise TypeError(f"diff_words() expects str for {name}, got {type(value).__name__}")
    # Compare token.text only: the offsets differ between the texts even for equal words.
    return edit_script(
        [token.text for token in _tokens.words(a)],
        [token.text for token in _tokens.words(b)],
    )
