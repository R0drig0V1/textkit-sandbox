"""HTML output rules of ``textkit.markdown``: escaping and the link-scheme allowlist.

Two decisions of the Markdown ADR (docs/decisions/*-markdown-subset-escaping-and-link-schemes.md)
live here so that the inline parser and the block writer apply them the same way:

- raw HTML is never passed through: ``&``, ``<``, ``>`` and ``"`` are escaped in every piece of
  text that reaches the output, code included (``escape``);
- a link keeps its URL only when it is relative or its scheme is ``http``, ``https`` or
  ``mailto``; any other scheme becomes ``#`` (``safe_url``).

This module has no dependencies on the rest of the package, so both ``inlines`` and
``render`` import it without a cycle.
"""

import unicodedata

# Schemes a link may keep, lower case. Everything else (javascript:, data:, vbscript:,
# file:, ...) is replaced: an allowlist cannot miss a dangerous scheme nobody thought of.
ALLOWED_SCHEMES = frozenset({"http", "https", "mailto"})

# The replacement for a URL whose scheme is not allowed: a link to the top of the page,
# harmless, and still a valid href so the link text renders as a link.
BLOCKED_URL = "#"

# Ampersand first, so the entities written by the later replacements are not escaped again.
_ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"))


def escape(text: str) -> str:
    """Escape ``&``, ``<``, ``>`` and ``"`` for HTML text and double-quoted attributes.

    ``'`` is left as is: textkit only writes double-quoted attributes, so it cannot end one.
    """
    for char, entity in _ESCAPES:
        text = text.replace(char, entity)
    return text


def _scheme_char_ignored(char: str) -> bool:
    """Whether ``char`` is dropped before the scheme is compared: whitespace or a control.

    Browsers remove tabs and newlines anywhere in a URL and strip leading controls and
    spaces, so ``"java\\tscript:"`` and ``" javascript:"`` both run script; removing them
    here makes the comparison see what a browser would see.
    """
    return char.isspace() or unicodedata.category(char) == "Cc"


def safe_url(url: str) -> str:
    """Return ``url`` if a link may point to it, else ``BLOCKED_URL`` (``"#"``).

    The scheme is the text before the first ``:``, with whitespace and control characters
    removed, compared case-insensitively with ``ALLOWED_SCHEMES``. A URL with no ``:`` has no
    scheme (it is relative) and is kept. A relative URL that contains a ``:`` anyway
    (``"/a?t=10:30"``) is treated as having a scheme and replaced: write the colon as
    ``%3A`` to keep it. The URL is returned unchanged, not escaped: escape it before writing
    it into an attribute.
    """
    if ":" not in url:
        return url
    scheme = "".join(c for c in url.split(":", 1)[0] if not _scheme_char_ignored(c))
    return url if scheme.lower() in ALLOWED_SCHEMES else BLOCKED_URL
