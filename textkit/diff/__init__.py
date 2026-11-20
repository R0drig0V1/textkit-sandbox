"""``textkit.diff``: line and word differences between texts (plan task T3.6).

Public functions (the names in ``__all__``, phase 3 rule "Packages"):

- ``unified_diff(a, b, context=3)``: the unified format of GNU ``diff -u`` (``unified.py``);
- ``apply_patch(text, patch)``: applies such a diff to a text (``patch.py``);
- ``diff_words(a, b)``: ``(op, word)`` pairs over the words of the two texts (``words.py``).

All three rest on ``lcs.py``, a longest common subsequence written for this package
(``difflib`` is not used). ``PatchError``, raised by ``apply_patch``, is importable from here
but is not in ``__all__``, which lists functions only. The format and the errors are in
``docs/diff.md``; the choices (no final newline, ties, cost) in the ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``.
"""

from textkit.diff.patch import PatchError, apply_patch
from textkit.diff.unified import unified_diff
from textkit.diff.words import diff_words

__all__ = ["apply_patch", "diff_words", "unified_diff"]
