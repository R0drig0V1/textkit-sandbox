<!-- 0006-what-is-an-email-address: what textkit.emails.is_email accepts (one @, local part and domain characters, dots, length limits). -->
# 0006. What counts as an email address

## Context

`textkit.emails.is_email(text)` (plan task T3.5) tells whether a string is an email address.
The full grammar of RFC 5322 (section 3.4.1) accepts far more than any mail provider or form
does: quoted local parts with spaces and `@` inside (`'"a b"@c.co'`, `'"a@b"@c.co'`),
comments in parentheses, address literals (`"a@[1.2.3.4]"`), and, with RFC 6531 (SMTPUTF8),
non-ASCII characters on both sides. A check that follows the whole grammar accepts addresses
that most systems reject, and a regular expression that tries to is unreadable. A check that
is too loose (`.+@.+`) accepts `"a@b"`, `".a@b.co"` and `"a@b.co."`. Checking that the domain
exists needs DNS, which a pure text helper must not do. So the rule has to be a small,
stated subset of the standard. Every case below is a test.

## Decision

`is_email` checks syntax only: no network access, no DNS lookup, no attempt to tell whether
the mailbox exists. A `str` is an address when all of the following hold, and `False` is
returned otherwise (it never raises for a `str`):

1. **One `@`.** The text contains exactly one `@`. The part before it is the *local part*,
   the part after it the *domain*. Because quoted local parts are rejected (rule 2), an `@`
   can never be part of the local part, so counting is enough.
2. **Local part: dot-atom.** The local part is the `dot-atom` of RFC 5322 section 3.2.3: one
   or more runs of *atext* joined by single dots. *atext* is the ASCII letters, the ASCII
   digits and the 20 symbols ``!#$%&'*+/=?^_`{|}~-``. So a leading, trailing or doubled dot
   is rejected (`".a@b.co"`, `"a.@b.co"`, `"a..b@c.co"`). Quoted strings (`'"a b"@c.co'`)
   and comments are not accepted.
3. **Domain: a host name.** The domain is two or more labels separated by single dots. Each
   label is 1 to 63 ASCII letters, digits and hyphens that does not start or end with a
   hyphen (the host-name rule of RFC 1123 section 2.1). The last label is not all digits.
   Rejected: one label (`"a@b"`), a trailing dot (`"a@b.co."`, the absolute DNS form), empty
   labels, underscores, and address literals (`"a@[1.2.3.4]"`).
4. **ASCII only.** Every character is ASCII. Internationalized local parts (RFC 6531) and
   domains written in Unicode are rejected: `"ü@b.co"` and `"a@bü.co"` are `False`. The
   ASCII form of an internationalized domain (`xn--` labels, IDNA) passes like any other
   label.
5. **Length limits.** The local part is at most 64 characters (RFC 5321 section 4.5.3.1.1);
   the whole address is at most 254 (RFC 5321 section 4.5.3.1.3 allows a 256-octet path,
   which includes the two angle brackets; RFC 3696 errata 1690). Each label is at most 63
   (rule 3). No separate limit on the domain is needed: with the shortest local part, 254
   leaves a domain of 252, under the 253 that DNS allows.
6. **Nothing is cleaned.** Whitespace is never stripped (`" a@b.co"` and `"a@b.co\n"` are
   `False`); letters of either case are accepted and kept as they are; no Unicode
   normalization is applied. A value that is not a `str` raises `TypeError`, as in the
   other helpers.

Why the last label may not be all digits: without it `"a@1.2.3.4"` would pass as a domain of
four labels, which is an IPv4 address written without the literal brackets, and no top-level
domain is numeric. Why address literals and quoted local parts are rejected rather than
supported: they are almost never used for real mailboxes, most providers refuse them, and
supporting them would make rule 1 (one `@`) and the character rules much harder to state.
This is close to the "valid e-mail address" of the HTML Living Standard, which also accepts
neither; unlike it, `is_email` rejects dots at the ends of the local part and one-label
domains, and enforces the length limits.

## Consequences

- Some addresses RFC 5322 allows are `False`: quoted local parts, address literals
  (`"a@[1.2.3.4]"`, `"a@[IPv6:::1]"`), comments, and one-label domains such as
  `"root@localhost"`. Accepted: they are rare outside a local network.
- Internationalized addresses (`"ü@b.co"`, `"a@bü.co"`) are `False`. A caller that needs
  them can convert the domain with the `idna` codec first; the local part has no such
  escape. Supporting SMTPUTF8 would be a new decision.
- `True` does not mean deliverable: `"a@example.invalid"` and `"a@nonexistent-domain.co"`
  are `True`. Checking that would need DNS or SMTP, which `textkit` does not do.
- Case is not changed or compared: `"A@B.CO"` is `True`, and whether two addresses are the
  same mailbox is out of scope.
- The rules are written with explicit ASCII character sets (not `\w` or `str.isalnum`,
  which accept non-ASCII letters and digits) and matched with `re.fullmatch` (not `$`,
  which accepts a trailing newline).

## Cases

Inputs are Python string literals. `tests/test_emails.py` tests every row and checks that this
table and its own case list stay identical; for the long rows its list holds the construction
given in the "Why" column, so the test also checks that each construction gives the literal.
The backtick and `|`, which a Markdown table cell cannot hold in a code span, are tested
separately there.

| Input | Result | Why |
|-------|--------|-----|
| `'a@b.co'` | True | the shortest common form |
| `'a.b@c.co'` | True | single dots inside the local part |
| `'A+tag_1-x@Sub-1.Example.COM'` | True | letters of any case, digits, `+`, `_`, `-`; hyphen inside a label |
| `"!#$%&'*+/=?^_{}~-@b.co"` | True | the atext symbols other than the backtick and `|` (tested separately) |
| `'a@b.c0'` | True | a last label with a letter is enough |
| `'.a@b.co'` | False | leading dot in the local part |
| `'a.@b.co'` | False | trailing dot in the local part |
| `'a..b@c.co'` | False | doubled dot in the local part |
| `'a@b'` | False | a domain of one label |
| `'a@b.co.'` | False | trailing dot in the domain |
| `'a@.b.co'` | False | leading dot in the domain |
| `'a@b..co'` | False | empty label |
| `'a@-b.co'` | False | label starting with a hyphen |
| `'a@b-.co'` | False | label ending with a hyphen |
| `'a@b_c.co'` | False | underscore in the domain |
| `'a@1.2.3.4'` | False | all-digit last label: a bare IPv4 address is not a domain |
| `'a@b.123'` | False | all-digit last label |
| `'"a b"@c.co'` | False | quoted local part |
| `'a@[1.2.3.4]'` | False | address literal |
| `'ü@b.co'` | False | non-ASCII local part |
| `'a@bü.co'` | False | non-ASCII domain (no IDN) |
| `'a@b@c.co'` | False | two `@` |
| `'a.b.co'` | False | no `@` |
| `'@b.co'` | False | empty local part |
| `'a@'` | False | empty domain |
| `' a@b.co'` | False | leading space: nothing is stripped |
| `'a@b.co\n'` | False | trailing newline |
| `'a b@c.co'` | False | space in the local part |
| `''` | False | empty text |
| `'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@b.co'` | True | `"a"*64 + "@b.co"`: a local part of 64, the limit |
| `'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@b.co'` | False | `"a"*65 + "@b.co"`: a local part of 65 |
| `'a@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.co'` | True | `"a@" + "b"*63 + ".co"`: a label of 63, the limit |
| `'a@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.co'` | False | `"a@" + "b"*64 + ".co"`: a label of 64 |
| `'a@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc'` | True | `"a@" + ".".join(["b"*63]*3) + "." + "c"*60`: 254 characters, the limit |
| `'a@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc'` | False | `"a@" + ".".join(["b"*63]*3) + "." + "c"*61`: 255 characters |
