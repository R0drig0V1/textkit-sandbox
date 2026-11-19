"""E-mail address helpers. Every public function is listed in the README's function table.

The accepted syntax is decided in docs/decisions/0003-is-email-accepted-syntax.md: a
deliberately strict, ASCII-only subset of RFC 5321/5322, checked offline (no network, no DNS).
"""

import re

# RFC 5322 "atext": the characters allowed in an unquoted local-part atom. Spelled out as
# ASCII ranges on purpose: no re.IGNORECASE (it would let the Kelvin sign U+212A match "k")
# and no \w (it accepts non-ASCII letters and digits).
_ATOM = "[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
# Dot-atom: atoms separated by single dots, no dot at either end.
_LOCAL_PART = re.compile(_ATOM + r"(?:\." + _ATOM + ")*")
# One DNS label: 1 to 63 letters, digits or hyphens, not starting or ending with a hyphen.
_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")

# RFC 5321 limits: 64 octets for the local part; 254 for the whole address (the 256-octet
# forward-path minus its angle brackets, RFC 3696 errata 1690). The domain's own limit is
# implied by the total.
_MAX_LOCAL = 64
_MAX_ADDRESS = 254


def is_email(text: str) -> bool:
    """Tell whether ``text`` is a syntactically valid e-mail address.

    Accepted: ``local@domain`` with exactly one ``@``, where ``local`` is a dot-atom of
    RFC 5322 atext characters (ASCII letters, digits and ``!#$%&'*+/=?^_`{|}~-``, single
    dots between atoms, none at either end) of at most 64 characters, and ``domain`` is at
    least two dot-separated DNS labels (1-63 ASCII letters, digits or hyphens, no hyphen at
    either end, no trailing dot) whose last label is not all digits. The whole address is at
    most 254 characters. Everything else returns ``False``: quoted local parts, address
    literals such as ``[1.2.3.4]``, non-ASCII characters, any whitespace (a trailing newline
    included). Nothing is looked up: no network and no DNS.

    Raises ``TypeError`` when ``text`` is not a ``str``; never raises for a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"is_email expects a str, got {type(text).__name__}")
    if len(text) > _MAX_ADDRESS or text.count("@") != 1:
        return False
    local, domain = text.split("@")
    if len(local) > _MAX_LOCAL or not _LOCAL_PART.fullmatch(local):
        return False
    labels = domain.split(".")
    if len(labels) < 2 or not all(_LABEL.fullmatch(label) for label in labels):
        return False
    # An all-digit top-level label would make "a@1.2.3.4" a bare IP address (RFC 3696 s2).
    # The labels are ASCII by now, so str.isdigit only sees ASCII digits.
    return not labels[-1].isdigit()
