"""Identifier case conversion. Every public function is listed in the README's function table.

How words are split inside an identifier (runs of capitals, digits) is fixed by
docs/decisions/0001-snake-case-word-boundaries.md; its case table is tested row by row in
tests/test_cases.py.
"""

import re

# Both patterns use explicit ASCII ranges on purpose: non-ASCII letters never create a word
# boundary (ADR 0001), and `[A-Z]` in a str pattern does not match them.

# The last capital of a run starts a new word when a lower-case letter follows it:
# "HTTPServer" -> "HTTP_Server".
_ACRONYM_THEN_WORD = re.compile(r"([A-Z])([A-Z][a-z])")
# A capital after a lower-case letter or a digit starts a new word:
# "camelCase" -> "camel_Case", "HTTP2Server" -> "HTTP2_Server".
_LOWER_OR_DIGIT_THEN_UPPER = re.compile(r"([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    """Convert a camelCase, PascalCase or kebab-case identifier to snake_case.

    Every ``-`` becomes ``_``; existing underscores are kept as they are, so snake_case input
    only gets lower-cased. A new ``_`` is inserted before a capital that follows a lower-case
    letter or a digit (``camelCase`` -> ``camel_case``) and before the last capital of a run
    when a lower-case letter follows it (``HTTPServer`` -> ``http_server``). Digits stay with
    the word before them (``parseURL2`` -> ``parse_url2``). The result is lower-cased.

    Only ASCII letters create word boundaries; any other character passes through, lower-cased
    by ``str.lower``. The rule and its known limits (plural acronyms such as ``URLs``) are in
    ADR 0001. ``""`` gives ``""``. Never raises for a ``str`` argument.
    """
    text = name.replace("-", "_")
    # Acronym boundary first: it only looks at capitals, so the second pass cannot undo it.
    text = _ACRONYM_THEN_WORD.sub(r"\1_\2", text)
    text = _LOWER_OR_DIGIT_THEN_UPPER.sub(r"\1_\2", text)
    return text.lower()
