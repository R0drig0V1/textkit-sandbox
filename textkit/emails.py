"""Email address helpers. Every public function is listed in the README's function table.

What ``is_email`` accepts is decided in docs/decisions/0006-what-is-an-email-address.md: a
syntax check of a practical, ASCII-only subset of RFC 5321/5322 addresses (dot-atom local
part, host-name domain of at least two labels), with no network access and no DNS lookup.
"""

import re

# atext of RFC 5322 section 3.2.3: ASCII letters, digits and these 20 symbols. Spelled out
# instead of \w or str.isalnum, which accept non-ASCII letters and digits the ADR rejects.
_ATEXT = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
# dot-atom: runs of atext joined by single dots, so no leading, trailing or doubled dot.
_LOCAL_PART = re.compile(rf"{_ATEXT}(?:\.{_ATEXT})*")
# A host-name label (RFC 1123): 1 to 63 ASCII letters, digits and hyphens, with a letter or
# digit at both ends. The length limit lives in the pattern so no separate check is needed.
_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")

# Length limits (RFC 5321 section 4.5.3.1 and its errata 1690: a path is at most 256
# octets including the two angle brackets, which leaves 254 for the address).
_MAX_LOCAL = 64
_MAX_ADDRESS = 254


def is_email(text: str) -> bool:
    """Return whether ``text`` is a syntactically valid email address.

    Only the syntax is checked: no network access, no DNS lookup, so a well-formed address
    at a domain that does not exist is still ``True``. Accepted, as decided in
    docs/decisions/0006-what-is-an-email-address.md:

    - exactly one ``@``, splitting ``text`` into a local part and a domain;
    - a local part of 1 to 64 characters: ASCII letters, digits and
      ``!#$%&'*+/=?^_`{|}~-``, with single dots between them (no leading, trailing or
      doubled dot); quoted local parts (``'"a b"@c.co'``) are rejected;
    - a domain of at least two dot-separated labels, each of 1 to 63 ASCII letters, digits
      and hyphens, not starting or ending with a hyphen, and a last label that is not all
      digits; no trailing dot, and no address literal (``"a@[1.2.3.4]"`` is ``False``);
    - at most 254 characters in all.

    Anything else gives ``False``: non-ASCII characters (no internationalized addresses),
    whitespace anywhere (nothing is stripped), the empty string. Letters of any case are
    accepted and the text is not normalized.

    Raises ``TypeError`` if ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"is_email() expects a str, got {type(text).__name__}")
    if len(text) > _MAX_ADDRESS or text.count("@") != 1:
        return False
    local, domain = text.split("@")
    if len(local) > _MAX_LOCAL or not _LOCAL_PART.fullmatch(local):
        return False
    labels = domain.split(".")
    # labels[-1].isdigit() only sees ASCII here: every label already matched _LABEL.
    return (
        len(labels) >= 2
        and all(_LABEL.fullmatch(label) for label in labels)
        and not labels[-1].isdigit()
    )
