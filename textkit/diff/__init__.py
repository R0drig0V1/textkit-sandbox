"""``textkit.diff``: unified line diffs, applying them, and word diffs (plan task T3.6).

Public functions (``__all__``): ``unified_diff`` (``unified.py``), the unified diff of two
texts as GNU ``diff -u`` writes it; ``apply_patch`` (``patch.py``), which applies such a
diff to a text; and ``diff_words`` (``words.py``), a word-by-word diff. All rest on
``lcs.py``, textkit's own longest common subsequence (no ``difflib``). ``PatchError`` is
importable from here but, being a class, is not in ``__all__`` (phase 3 rule "Packages").
Format and errors: ``docs/diff.md``; decisions: the ADR
``docs/decisions/*-unified-diff-newlines-ties-and-cost.md``.
"""

from textkit.diff.patch import PatchError, apply_patch
from textkit.diff.unified import unified_diff
from textkit.diff.words import diff_words

__all__ = ["apply_patch", "diff_words", "unified_diff"]
